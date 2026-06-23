import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from team_finder.constants import SKILL_NAME_MAX_LENGTH, SKILLS_SUGGEST_LIMIT
from team_finder.pagination import get_page_obj

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    active_skill = request.GET.get("skill", "").strip()
    projects = Project.objects.select_related("owner").prefetch_related("participants", "skills")

    if active_skill:
        projects = projects.filter(skills__name=active_skill)

    page_obj = get_page_obj(projects.distinct(), request.GET.get("page"))
    all_skills = Skill.objects.values_list("name", flat=True)

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj.object_list,
            "all_skills": all_skills,
            "active_skill": active_skill,
            "page_obj": page_obj,
        },
    )


def project_detail(request, project_pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants", "skills"),
        pk=project_pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    if request.method != "POST":
        return render(
            request,
            "projects/create-project.html",
            {"form": ProjectForm(), "is_edit": False},
        )

    form = ProjectForm(request.POST)
    if not form.is_valid():
        return render(request, "projects/create-project.html", {"form": form, "is_edit": False})

    project = form.save(commit=False)
    project.owner = request.user
    project.save()
    project.participants.add(request.user)
    return redirect("projects:detail", project_pk=project.pk)


@login_required
def edit_project(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if project.owner != request.user:
        return HttpResponseForbidden("Редактировать проект может только автор.")

    if request.method != "POST":
        return render(
            request,
            "projects/create-project.html",
            {"form": ProjectForm(instance=project), "is_edit": True},
        )

    form = ProjectForm(request.POST, instance=project)
    if not form.is_valid():
        return render(request, "projects/create-project.html", {"form": form, "is_edit": True})

    project = form.save()
    return redirect("projects:detail", project_pk=project.pk)


@login_required
@require_POST
def complete_project(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "error": "Завершить проект может только автор."},
            status=HTTPStatus.FORBIDDEN,
        )

    if project.status != Project.STATUS_CLOSED:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=["status"])

    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def toggle_participate(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if project.owner == request.user:
        return JsonResponse(
            {"status": "error", "error": "Автор проекта уже участвует в нём."},
            status=HTTPStatus.BAD_REQUEST,
        )

    participant = not project.participants.filter(pk=request.user.pk).exists()
    if participant:
        project.participants.add(request.user)
    else:
        project.participants.remove(request.user)

    return JsonResponse({"status": "ok", "participant": participant})


@require_GET
def skills_search(request):
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=query)[:SKILLS_SUGGEST_LIMIT]
    return JsonResponse([{"id": skill.pk, "name": skill.name} for skill in skills], safe=False)


@login_required
@require_POST
def add_project_skill(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "error": "Добавлять навыки может только автор проекта."},
            status=HTTPStatus.FORBIDDEN,
        )

    data = _request_data(request)
    skill = None
    created = False
    skill_pk = data.get("skill_id")
    name = str(data.get("name", "")).strip()

    if skill_pk:
        skill = get_object_or_404(Skill, pk=skill_pk)
    elif name:
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            skill = Skill.objects.create(name=name[:SKILL_NAME_MAX_LENGTH])
            created = True
    else:
        return JsonResponse(
            {"status": "error", "error": "Укажите название навыка."},
            status=HTTPStatus.BAD_REQUEST,
        )

    already_added = project.skills.filter(pk=skill.pk).exists()
    if not already_added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.pk,
            "name": skill.name,
            "skill_id": skill.pk,
            "created": created,
            "added": not already_added,
        }
    )


@login_required
@require_POST
def remove_project_skill(request, project_pk, skill_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if project.owner != request.user:
        return JsonResponse(
            {"status": "error", "error": "Удалять навыки может только автор проекта."},
            status=HTTPStatus.FORBIDDEN,
        )

    skill = get_object_or_404(Skill, pk=skill_pk)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse(
            {"status": "error", "error": "У проекта нет такого навыка."},
            status=HTTPStatus.NOT_FOUND,
        )

    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})


def _request_data(request):
    if request.content_type.startswith("application/json"):
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST
