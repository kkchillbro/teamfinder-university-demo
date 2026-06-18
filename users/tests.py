import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserAuthTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Анна",
                "surname": "Иванова",
                "email": "anna@example.com",
                "password": "strong-pass-123",
            },
        )

        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(get_user_model().objects.filter(email="anna@example.com").exists())

    def test_login_uses_email_and_password(self):
        get_user_model().objects.create_user(
            email="ivan@example.com",
            password="strong-pass-123",
            name="Иван",
            surname="Петров",
        )

        response = self.client.post(
            reverse("users:login"),
            {"email": "ivan@example.com", "password": "strong-pass-123"},
        )

        self.assertRedirects(response, reverse("projects:list"))
