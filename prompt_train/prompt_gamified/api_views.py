from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from rest_framework.views import APIView

from prompt_train.oauth_secret import oauth
from users.models import CustomUser


class GoogleLoginView(APIView):
    def get(self, request):
        redirect_url = 'http://localhost:8000/auth/google/callback/' # Має бути в Authorized redirect URIs
        # Створення правильного url з даними oauth-клієнта
        return oauth.google.authorize_redirect(request, redirect_url)
    

class GoogleCallbackView(APIView):
    def get(self, request):
        token = oauth.google.authorize_access_token(request)
        # Отримання даних користувача
        response = oauth.google.get(
            'https://openidconnect.googleapis.com/v1/userinfo',
            token=token
        )
        user_info = response.json()

        email = user_info['email']
        nickname = user_info.get('nickname', '')
        sub = user_info.get('sub') # Зовнішній ідентифікатор

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'nickname': nickname
            }
        )

        login(request, user)
        response = redirect('http://localhost:8000')
        response.set_cookie(
            key="google_registration_success",
            value=1,
            max_age=60 * 60 * 24,
            httponly=True,
            # Cookie передається лише в безпечних навігаційних запитах
            samesite="Lax", 
            secure= not settings.DEBUG,
        )
        messages.success(request, "Реєстрація успішна!")

        return response