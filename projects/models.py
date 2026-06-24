from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from team_finder.constants import PROJECT_NAME_MAX_LENGTH, SKILL_NAME_MAX_LENGTH
from team_finder.validators import validate_github_url


class Skill(models.Model):
    name = models.CharField(_("название"), max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("навык")
        verbose_name_plural = _("навыки")

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, _("Открыт")),
        (STATUS_CLOSED, _("Закрыт")),
    ]

    name = models.CharField(_("название"), max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField(_("описание"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name=_("автор"),
    )
    created_at = models.DateTimeField(_("дата создания"), auto_now_add=True)
    github_url = models.URLField(
        _("ссылка на GitHub"),
        blank=True,
        validators=[validate_github_url],
    )
    status = models.CharField(
        _("статус"),
        max_length=max(len(status) for status, _ in STATUS_CHOICES),
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="participated_projects",
        verbose_name=_("участники"),
    )
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="projects",
        verbose_name=_("навыки"),
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("проект")
        verbose_name_plural = _("проекты")

    def __str__(self):
        return self.name
