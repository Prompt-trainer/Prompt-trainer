from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.views import View

from prompt_train.oauth import oauth
from users.models import CustomUser
from random import randint

class GoogleLoginView(View):
    def get(self, request):
        callback_path = reverse("prompt_gamified:google_callback")
        redirect_url = request.build_absolute_uri(callback_path)
        return oauth.google.authorize_redirect(request, redirect_url)


class GoogleCallbackView(View):
    def get(self, request):
        token = oauth.google.authorize_access_token(request)

        # бажано переконатися, що в конфізі є scope "openid email profile" [web:2][web:3][web:5]
        response = oauth.google.get(
            "https://openidconnect.googleapis.com/v1/userinfo", token=token
        )
        user_info = response.json()

        email = user_info["email"]
        sub = user_info.get("sub")

        # побудова "нікнейму" з нормальними fallback-ами
        name = (
            user_info.get("name")
            or user_info.get("given_name")
            or email.split("@")[0]
        )
        while CustomUser.objects.filter(nickname=name).exists():
            name = f"{name}{randint(1, 9999)}"

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={"nickname": name},
        )

        # якщо користувач уже існує, можна (за бажання) оновити нік тільки якщо він порожній
        if not created and not user.nickname:
            user.nickname = name

        user.is_active = True
        user.save()

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        response = redirect("prompt_gamified:home_page")
        response.set_cookie(
            key="google_registration_success",
            value=1,
            max_age=60 * 60 * 24,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
        )

        messages.success(request, "Реєстрація успішна!")
        return response
