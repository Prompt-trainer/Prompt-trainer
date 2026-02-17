from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib import messages
import random

from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
        return super().pre_social_login(request, sociallogin)

    def is_auto_signup_allowed(self, request, sociallogin):
        """Дозволяє автоматичну автентифікацію без створення форми."""
        return True

    def populate_user(self, request, sociallogin, data):
        """Заповнює nickname перед збереженням."""
        user = super().populate_user(request, sociallogin, data)

        # Отримання додаткових даних з GitHub API
        github_username = sociallogin.account.extra_data.get("login")

        # Створення nickname по логіну, інакше бере з email частину перед '@'
        base_nickname = github_username or user.email.split("@")[0]

        from users.models import CustomUser

        nickname = base_nickname
        counter = 1

        # Якщо nickname зайнятий, додається число в кінець
        while CustomUser.objects.filter(nickname=nickname).exists():
            nickname = f"{base_nickname}{counter}"
            counter += random.randint(1, 9)

        user.nickname = nickname
        user.is_active = True

        return user
