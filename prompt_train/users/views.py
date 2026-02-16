from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.conf import settings
from .forms import RegistrationForm
from .tasks import send_registration_email_task
from django.utils import timezone


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
