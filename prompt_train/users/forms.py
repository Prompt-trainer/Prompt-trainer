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


class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["email", "nickname", "profile_picture"]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True
        self.fields['profile_picture'].label = 'Фото профілю'