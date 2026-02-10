from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["email", "nickname", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.save()
        return user
