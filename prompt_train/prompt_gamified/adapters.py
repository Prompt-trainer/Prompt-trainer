from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from random import randint
import random


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
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
