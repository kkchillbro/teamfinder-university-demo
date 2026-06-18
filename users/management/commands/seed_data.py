from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from projects.models import Project, Skill


class Command(BaseCommand):
    help = "Creates demo users, projects and skills for reviewer checks."

    def handle(self, *args, **options):
        User = get_user_model()
        demo_users = [
            {
                "email": "anna@example.com",
                "name": "Анна",
                "surname": "Иванова",
                "about": "Backend-разработчик, люблю API и аккуратные модели.",
                "phone": "+79000000001",
                "github_url": "https://github.com/anna",
            },
            {
                "email": "ivan@example.com",
                "name": "Иван",
                "surname": "Петров",
                "about": "Frontend-разработчик, собираю интерфейсы для pet-проектов.",
                "phone": "+79000000002",
                "github_url": "https://github.com/ivan",
            },
            {
                "email": "maria@example.com",
                "name": "Мария",
                "surname": "Соколова",
                "about": "Дизайнер продукта и исследователь пользовательских сценариев.",
                "phone": "+79000000003",
                "github_url": "https://github.com/maria",
            },
        ]

        users = []
        for data in demo_users:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "name": data["name"],
                    "surname": data["surname"],
                    "about": data["about"],
                    "phone": data["phone"],
                    "github_url": data["github_url"],
                },
            )
            if created:
                user.set_password("teamfinder123")
                user.save()
            users.append(user)

        skills = {
            name: Skill.objects.get_or_create(name=name)[0]
            for name in ["Django", "PostgreSQL", "React", "UX", "Docker", "API"]
        }

        project_specs = [
            (
                users[0],
                "API для волонтерских команд",
                "Сервис помогает волонтерам быстро находить задачи, собирать команды и вести статусы.",
                "https://github.com/anna/volunteer-api",
                ["Django", "PostgreSQL", "API"],
            ),
            (
                users[1],
                "Доска идей для хакатонов",
                "Интерфейс для публикации идей, поиска участников и быстрого старта команд.",
                "https://github.com/ivan/hack-board",
                ["React", "API"],
            ),
            (
                users[2],
                "Планировщик пользовательских интервью",
                "Инструмент для дизайнеров и продуктовых команд, которые проводят интервью.",
                "https://github.com/maria/interview-planner",
                ["UX", "Docker"],
            ),
        ]

        for owner, name, description, github_url, skill_names in project_specs:
            project, _ = Project.objects.get_or_create(
                owner=owner,
                name=name,
                defaults={"description": description, "github_url": github_url},
            )
            project.participants.add(owner)
            project.skills.set([skills[skill_name] for skill_name in skill_names])

        self.stdout.write(self.style.SUCCESS("Demo data is ready. Password: teamfinder123"))
