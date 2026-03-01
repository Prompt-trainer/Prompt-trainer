from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.conf import settings
from django.views import View
from django.urls import reverse
from random import randint

from prompt_train.oauth import oauth
from .forms import RegistrationForm, CustomUserForm
from .models import UserCosmetic
from users.models import CustomUser


# Common registration

def register_view(request):
    form = RegistrationForm()
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')


            response = redirect("prompt_gamified:home_page")
            response.set_cookie(
                key="registration_success",
                value="1",
                max_age=60 * 60 * 24,
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
            )

            messages.success(request, "Реєстрація успішна!")
            return response
    return render(request, "users/register.html", {"form": form})


# Google registration

class GoogleLoginView(View):
    def get(self, request):
        callback_path = reverse("auth:google_callback")
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

        # якщо користувач уже існує, можна (за бажанням) оновити нік тільки якщо він порожній
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


# Profile

@login_required
def profile_view(request):
    return render(request, "users/profile.html")


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль успішно оновлено!")
            return redirect("auth:profile")
    else:
        form = CustomUserForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def delete_profile_view(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        return redirect("auth:login")
    return redirect("auth:profile")


# User cosmetics

@login_required
def user_cosmetics_view(request):
    user_cosmetics = UserCosmetic.objects.filter(user=request.user).select_related('cosmetic').order_by('cosmetic__type', 'purchase_date')
    active_cosmetics_ids = set()
    if request.user.active_ring_id:
        active_cosmetics_ids.add(request.user.active_ring_id)
    if request.user.active_title_id:
        active_cosmetics_ids.add(request.user.active_title_id)
    if request.user.active_element_id:
        active_cosmetics_ids.add(request.user.active_element_id)
    return render(request, "users/user_cosmetics.html", {"user_cosmetics": user_cosmetics, "active_cosmetics_ids": active_cosmetics_ids})


@login_required
def activate_cosmetic_view(request, user_cosmetic_id):
    if request.method == "POST":
        user_cosmetic = UserCosmetic.objects.get(id=user_cosmetic_id, user=request.user)
        user_cosmetic.activate_cosmetic()
        messages.success(request, "Елемент оформлення успішно активовано!")

    return redirect("auth:user_cosmetics")


@login_required
def take_off_cosmetic_view(request, user_cosmetic_id):
    if request.method == "POST":
        user_cosmetic = UserCosmetic.objects.get(id=user_cosmetic_id, user=request.user)
        user_cosmetic.take_off_cosmetic()
        messages.success(request, "Елемент оформлення успішно знято!")
    return redirect("auth:user_cosmetics")