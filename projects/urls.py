from django.urls import path

from . import views


app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="index"),
    path("list/", views.project_list, name="list"),
    path("create-project/", views.create_project, name="create"),
    path("skills/", views.skills_search, name="skills_search"),
    path("<int:project_pk>/", views.project_detail, name="detail"),
    path("<int:project_pk>/edit/", views.edit_project, name="edit"),
    path("<int:project_pk>/complete/", views.complete_project, name="complete"),
    path(
        "<int:project_pk>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path("<int:project_pk>/skills/add/", views.add_project_skill, name="add_skill"),
    path(
        "<int:project_pk>/skills/<int:skill_pk>/remove/",
        views.remove_project_skill,
        name="remove_skill",
    ),
]
