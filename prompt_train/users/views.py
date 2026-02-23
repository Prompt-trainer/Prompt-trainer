from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import RegistrationForm, CustomUserForm
from .models import Cosmetic, UserCosmetic



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