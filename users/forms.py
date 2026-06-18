import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(self.request, username=email.lower(), password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный email или пароль.")
            if not self.user.is_active:
                raise forms.ValidationError("Аккаунт заблокирован.")

        return cleaned_data

    def get_user(self):
        return self.user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "avatar": forms.FileInput(attrs={"style": "display: none;"}),
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone:
            return None

        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("8"):
            phone = "+7" + phone[1:]

        if not re.fullmatch(r"\+7\d{10}", phone):
            raise forms.ValidationError("Введите телефон в формате 8XXXXXXXXXX или +7XXXXXXXXXX.")

        users = User.objects.filter(phone=phone)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError("Этот телефон уже указан у другого пользователя.")

        return phone

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if not url:
            return url

        host = urlparse(url).netloc.lower().removeprefix("www.")
        if host != "github.com" and not host.endswith(".github.com"):
            raise forms.ValidationError("Ссылка должна вести на GitHub.")
        return url


class UserPasswordChangeForm(PasswordChangeForm):
    pass
