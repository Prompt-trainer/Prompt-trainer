from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from users.models import CustomUser
from .models import Prompt
from django.db import transaction
from django.core.paginator import Paginator
import random
from django.db import transaction
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
    paginator = Paginator(users_list, 10)

    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    start_rank = (page_obj.number - 1) * paginator.per_page
    for idx, user in enumerate(page_obj.object_list, start=1):
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
