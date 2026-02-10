from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView

from prompt_train.oauth import oauth
from users.models import CustomUser


class GoogleLoginView(APIView):
    def get(self, request):
        callback_path = reverse("prompt_gamified:google_callback")
        redirect_url = request.build_absolute_uri(callback_path)
        return oauth.google.authorize_redirect(request, redirect_url)


class GoogleCallbackView(APIView):
    def get(self, request):
        token = oauth.google.authorize_access_token(request)
        # Отримання даних користувача
        response = oauth.google.get(
            "https://openidconnect.googleapis.com/v1/userinfo", token=token
        )
        user_info = response.json()

        email = user_info["email"]
        nickname = user_info.get("nickname", "")
        sub = user_info.get("sub")  # Зовнішній ідентифікатор

        user, created = CustomUser.objects.get_or_create(
            email=email, defaults={"nickname": nickname}
        )

        login(request, user)
        response = redirect("prompt_gamified:home_page")
        response.set_cookie(
            key="google_registration_success",
            value=1,
            max_age=60 * 60 * 24,
            httponly=True,
            # Cookie передається лише в безпечних навігаційних запитах
            samesite="Lax",
            secure=not settings.DEBUG,
        )
        messages.success(request, "Реєстрація успішна!")

        return response
