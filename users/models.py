import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageDraw, ImageFont

from team_finder.constants import (
    AVATAR_FONT_SIZE,
    AVATAR_IMAGE_SIZE,
    AVATAR_PALETTE,
    AVATAR_SIZE_PX,
    AVATAR_VERTICAL_OFFSET,
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
)
from team_finder.validators import validate_github_url


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("surname", "User")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("электронная почта"), unique=True)
    name = models.CharField(_("имя"), max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(_("фамилия"), max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(_("аватар"), upload_to="avatars/", blank=True)
    phone = models.CharField(
        _("телефон"),
        max_length=USER_PHONE_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
    )
    github_url = models.URLField(
        _("ссылка на GitHub"),
        blank=True,
        validators=[validate_github_url],
    )
    about = models.TextField(_("о себе"), max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField(_("активен"), default=True)
    is_staff = models.BooleanField(_("сотрудник"), default=False)
    date_joined = models.DateTimeField(_("дата регистрации"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["surname", "name", "email"]
        verbose_name = _("пользователь")
        verbose_name_plural = _("пользователи")

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.name} {self.surname}".strip()

    def get_short_name(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.avatar and self.name:
            self.avatar.save(self._avatar_filename(), self._avatar_content(), save=False)
        super().save(*args, **kwargs)

    def _avatar_filename(self):
        return f"avatar_{uuid.uuid4()}.png"

    def _avatar_content(self):
        color = AVATAR_PALETTE[ord(self.name[0].upper()) % len(AVATAR_PALETTE)]
        image = Image.new("RGB", AVATAR_IMAGE_SIZE, color)
        draw = ImageDraw.Draw(image)
        letter = self.name[0].upper()

        try:
            font = ImageFont.truetype("Arial.ttf", AVATAR_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (
            (AVATAR_SIZE_PX - text_width) / 2,
            (AVATAR_SIZE_PX - text_height) / 2 - AVATAR_VERTICAL_OFFSET,
        )
        draw.text(position, letter, fill="white", font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
