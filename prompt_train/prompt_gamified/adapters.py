from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib import messages
import random

from django.contrib.auth import get_user_model

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
        base_nickname = github_username or (
            user.email.split("@")[0] if user.email else "user")

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
    
    def pre_social_login(self, request, sociallogin):
        """Підключає GitHub до існуючого користувача або створює нового."""
        # Логінимо в разі наявності зв'язаного акаунту
        if sociallogin.is_existing:
            return
        
        from allauth.socialaccount.models import SocialAccount
        from .models import CustomUser
        # Шукаємо існуючий socialaccount у бд
        try:
            existing = SocialAccount.objects.get(
                provider=sociallogin.account.provider,
                uid=sociallogin.account.uid
            )
            # Якщо знайшли, підключаємо GitHub до існуючого користувача
            sociallogin.connect(request, existing.user)
        except SocialAccount.DoesNotExist:
            pass

        # Отримаємо email з extra_data, якщо у користувача email публічний
        email = sociallogin.account.extra_data.get("email") or (
            # Інакше отримаємо зі списку адрес
            sociallogin.email_addresses[0].email
            if sociallogin.email_addresses else None
        )
        if email:
            # Шукаємо користувача з email у бд
            try:
                existing_user = CustomUser.objects.get(email=email)
                # У разі знаходження підключаємо до існуючого користувача
                sociallogin.connect(request, existing_user)
            # Інакше створюємо нового користувача
            except CustomUser.DoesNotExist:
                pass
