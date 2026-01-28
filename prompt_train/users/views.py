from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .forms import RegistrationForm
from .tasks import send_registration_email_task
from django.utils import timezone


def register_view(request):
    """Реєстрація нового користувача"""
    form = RegistrationForm()
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            login(request, user)
            # Відправити вітальний email через Celery
            send_registration_email_task.delay(user.id)
            
            response = redirect("auth:login")
            messages.success(request, "Реєстрація пройшла успішно! Ви можете увійти в систему.")
            return response
    return render(request, "users/register.html", {"form": form})


