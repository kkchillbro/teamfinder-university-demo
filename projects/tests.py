import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Project, Skill


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="strong-pass-123",
            name="Ольга",
            surname="Авторова",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="strong-pass-123",
            name="Максим",
            surname="Участников",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Командный сервис",
            description="Описание проекта",
        )
        self.project.participants.add(self.owner)
        self.skill = Skill.objects.create(name="Django")
        self.project.skills.add(self.skill)

    def test_project_list_filters_by_skill(self):
        other = Project.objects.create(owner=self.member, name="Дизайн-система")
        other.participants.add(self.member)

        response = self.client.get(reverse("projects:list"), {"skill": "Django"})

        self.assertContains(response, self.project.name)
        self.assertNotContains(response, other.name)

    def test_only_owner_can_add_project_skill(self):
        self.client.login(email="member@example.com", password="strong-pass-123")
        response = self.client.post(
            reverse("projects:add_skill", args=[self.project.pk]),
            data=json.dumps({"name": "PostgreSQL"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.login(email="owner@example.com", password="strong-pass-123")
        response = self.client.post(
            reverse("projects:add_skill", args=[self.project.pk]),
            data=json.dumps({"name": "PostgreSQL"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.project.skills.filter(name="PostgreSQL").exists())

    def test_authenticated_user_can_toggle_participation(self):
        self.client.login(email="member@example.com", password="strong-pass-123")
        response = self.client.post(reverse("projects:toggle_participate", args=[self.project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["participant"])
        self.assertTrue(self.project.participants.filter(pk=self.member.pk).exists())
