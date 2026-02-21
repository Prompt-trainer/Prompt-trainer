from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from users.models import CustomUser
from .models import Prompt, Cosmetic, UserCosmetic
from django.db import transaction
import random
from .utils import (
    handle_challenge_get,
    handle_challenge_post,
    handle_guess_the_best_prompt_get,
    handle_guess_the_best_prompt_post,
    handle_prompt_trainer_post,
)

def index_view(request):
    return render(request, "prompt_gamified/index.html")

@login_required
def home_view(request):
    return render(request, "prompt_gamified/home.html")


@login_required
def good_prompts_view(request):
    # Показуємо перші 100 промптів, починаючи з найкращого
    prompts = Prompt.objects.all().order_by("-rate")[:100]
    return render(request, "prompt_gamified/good_prompts.html", {"prompts": prompts})


@login_required
def prompt_trainer_view(request):
    context = {}

    if request.method == "POST":
        user_message = request.POST.get("prompt", "")
        context, error = handle_prompt_trainer_post(request.user, user_message)

        if error:
            context["error"] = error

    return render(request, "prompt_gamified/prompt_trainer.html", context)


@login_required
def leaderboard_view(request):
    users_list = CustomUser.objects.filter(is_active=True).order_by("-exp")
    # 10 - максимальна кількість користувачів на сторінці
    paginator = Paginator(users_list, 10)

    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Задаємо позицію першого користувача на сторінці
    start_rank = (page_obj.number - 1) * paginator.per_page

    # Перебираємо позицію користувача на сторінці та починаємо з 1
    for idx, user in enumerate(page_obj.object_list, start=1):
        # Визначаємо глобальну позицію користувача.
        # Наприклад, на сторінці 5 користувач із позицією 4 буде
        # (5-1) * 10 + 4 = 44-м у глобальному рейтингу
        user.rank_position = start_rank + idx

    context = {
        "page_obj": page_obj,
        "total_users": paginator.count,
    }
    return render(request, "prompt_gamified/leader_board.html", context)


@login_required
def challenge_view(request):
    if request.method == "GET":
        context = handle_challenge_get(request)
    else:
        context = handle_challenge_post(request)
        if context is None:
            return redirect("prompt_gamified:challenge")

    return render(request, "prompt_gamified/challenge.html", context)


@login_required
def guess_the_best_prompt_view(request):
    if request.method == "GET":
        context = handle_guess_the_best_prompt_get(request)
    else:
        context = handle_guess_the_best_prompt_post(request)
        if context is None:
            return redirect("prompt_gamified:guess_the_best_prompt")

    return render(request, "prompt_gamified/guess_the_best_prompt.html", context)


def store_view(request):
    # Відображаємо елементи косметики всіх типів, окрім рангових кілець
    cosmetics = Cosmetic.objects.filter(type__in=["ring", "element", "title"])

    # Отримуємо список id елментів косметики, купленної користувачем
    purchased_ids = set(
        UserCosmetic.objects.filter(user=request.user)
        .values_list("cosmetic_id", flat=True)
    )

    context = {
        "cosmetics": cosmetics,
        "purchased_ids": purchased_ids,
    }
    return render(request, "prompt_gamified/store.html", context)


def buy_cosmetic_view(request, cosmetic_id):
    cosmetic = Cosmetic.objects.get(id=cosmetic_id)
    try:
        request.user.buy_cosmetic(cosmetic)
        messages.success(request, "Елемент косметики успішно придбано!")
    except ValidationError as e:
        for message in e.messages:
            messages.error(request, message)

    return redirect("prompt_gamified:store")
