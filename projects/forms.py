from urllib.parse import urlparse

from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "GitHub",
            "status": "Статус",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["github_url"].required = False
        self.fields["status"].choices = [
            (Project.STATUS_OPEN, "Открыт"),
            (Project.STATUS_CLOSED, "Закрыт"),
        ]

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if not url:
            return url

        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host != "github.com" and not host.endswith(".github.com"):
            raise forms.ValidationError("Ссылка должна вести на GitHub.")
        return url
