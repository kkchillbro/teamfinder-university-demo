import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
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
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(max_length=12, unique=True, blank=True, null=True)
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["-id"]

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
        from PIL import Image, ImageDraw, ImageFont

        palette = ["#2f80ed", "#27ae60", "#9b51e0", "#eb5757", "#f2994a", "#00a3a3"]
        color = palette[ord(self.name[0].upper()) % len(palette)]
        image = Image.new("RGB", (160, 160), color)
        draw = ImageDraw.Draw(image)
        letter = self.name[0].upper()

        try:
            font = ImageFont.truetype("Arial.ttf", 90)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((160 - text_width) / 2, (160 - text_height) / 2 - 6)
        draw.text(position, letter, fill="white", font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())
