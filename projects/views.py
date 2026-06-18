import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    active_skill = request.GET.get("skill", "").strip()
    projects = (
        Project.objects.select_related("owner")
        .prefetch_related("participants", "skills")
        .order_by("-created_at")
    )

    if active_skill:
        projects = projects.filter(skills__name=active_skill)

    paginator = Paginator(projects.distinct(), 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    all_skills = Skill.objects.order_by("name").values_list("name", flat=True)

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


def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants", "skills"),
        pk=pk,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", pk=project.pk)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return HttpResponseForbidden("Редактировать проект может только автор или администратор.")

    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        return redirect("projects:detail", pk=project.pk)

    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@require_POST
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "error": "forbidden"}, status=403)

    if project.status != Project.STATUS_CLOSED:
        project.status = Project.STATUS_CLOSED
        project.save(update_fields=["status"])

    return JsonResponse({"status": "ok", "project_status": Project.STATUS_CLOSED})


@require_POST
def toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "error": "auth_required"}, status=403)
    if project.owner_id == request.user.id:
        return JsonResponse({"status": "error", "error": "owner_cannot_leave"}, status=400)

    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True

    return JsonResponse({"status": "ok", "participant": participant})


@require_GET
def skills_search(request):
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=query).order_by("name")[:10]
    return JsonResponse([{"id": skill.id, "name": skill.name} for skill in skills], safe=False)


@require_POST
def add_project_skill(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "error": "forbidden"}, status=403)

    data = _request_data(request)
    skill = None
    created = False

    skill_id = data.get("skill_id")
    name = str(data.get("name", "")).strip()

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    elif name:
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            skill = Skill.objects.create(name=name[:124])
            created = True
    else:
        return JsonResponse({"status": "error", "error": "empty_skill"}, status=400)

    already_added = project.skills.filter(pk=skill.pk).exists()
    if not already_added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.id,
            "name": skill.name,
            "skill_id": skill.id,
            "created": created,
            "added": not already_added,
        }
    )


@require_POST
def remove_project_skill(request, pk, skill_id):
    project = get_object_or_404(Project, pk=pk)
    if not _can_manage_project(request.user, project):
        return JsonResponse({"status": "error", "error": "forbidden"}, status=403)

    skill = get_object_or_404(Skill, pk=skill_id)
    if not project.skills.filter(pk=skill.pk).exists():
        return JsonResponse({"status": "error", "error": "skill_not_in_project"}, status=404)

    project.skills.remove(skill)
    return JsonResponse({"status": "ok", "removed": True})


def _can_manage_project(user, project):
    return user.is_authenticated and (project.owner_id == user.id or user.is_staff)


def _request_data(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST
