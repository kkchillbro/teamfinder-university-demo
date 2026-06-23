from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.pagination import get_page_obj

from .forms import LoginForm, ProfileForm, RegisterForm


User = get_user_model()


def participants_list(request):
    users = User.objects.filter(is_active=True)
    page_obj = get_page_obj(users, request.GET.get("page"))
    return render(
        request,
        "users/participants.html",
        {"participants": page_obj.object_list, "page_obj": page_obj},
    )


def user_detail(request, user_pk):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants"),
        pk=user_pk,
        is_active=True,
    )
    return render(request, "users/user-details.html", {"user": profile_user})


def register(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    if request.method != "POST":
        return render(request, "users/register.html", {"form": RegisterForm()})

    form = RegisterForm(request.POST)
    if not form.is_valid():
        return render(request, "users/register.html", {"form": form})

    form.save()
    return redirect("users:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    if request.method != "POST":
        return render(request, "users/login.html", {"form": LoginForm(request)})

    form = LoginForm(request, request.POST)
    if not form.is_valid():
        return render(request, "users/login.html", {"form": form})

    login(request, form.get_user())
    return redirect("projects:list")


def logout_view(request):
    logout(request)
    return redirect("projects:list")


@login_required
def edit_profile(request):
    if request.method != "POST":
        return render(
            request,
            "users/edit_profile.html",
            {"form": ProfileForm(instance=request.user)},
        )

    form = ProfileForm(request.POST, request.FILES, instance=request.user)
    if not form.is_valid():
        return render(request, "users/edit_profile.html", {"form": form})

    form.save()
    return redirect("users:detail", user_pk=request.user.pk)


@login_required
def change_password(request):
    if request.method != "POST":
        return render(
            request,
            "users/change_password.html",
            {"form": PasswordChangeForm(request.user)},
        )

    form = PasswordChangeForm(request.user, request.POST)
    if not form.is_valid():
        return render(request, "users/change_password.html", {"form": form})

    user = form.save()
    update_session_auth_hash(request, user)
    return redirect("users:detail", user_pk=request.user.pk)
