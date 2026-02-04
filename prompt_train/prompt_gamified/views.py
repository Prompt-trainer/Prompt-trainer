from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from users.models import CustomUser
from .ai_func import evaluate_prompt_quality
from django.http import JsonResponse
from .models import Prompt
from django.db import transaction
from django.core.paginator import Paginator

def index_view(request):
    return render(request, "prompt_gamified/index.html")


@login_required
def home_view(request):
    return render(request, "prompt_gamified/home.html")

@login_required
def good_prompts_view(request):
    prompts = Prompt.objects.all().order_by('-rate')[:100]
    return render(request, "prompt_gamified/good_prompts.html", {"prompts": prompts})

@login_required
def prompt_trainer_view(request):
    context = {}

    if request.method == "POST":
        user_message = request.POST.get("prompt", "").strip()

        if user_message:
            length = len(user_message)
            if length > 500:
                raise Exception("Промпт має бути не менше 500 символів.")
            else:
                rate, improvement_hint, refined_prompt = evaluate_prompt_quality(user_message)
            Prompt.objects.create(
                prompt_text=user_message,
                improvement_hint=improvement_hint,
                rate=rate,
                user=request.user,
            )
            user = request.user
            updated_fields = []

            if rate > 7:
                user.exp += 1
                updated_fields.append("exp")

            if rate >= 8:
                user.points += 20
                updated_fields.append("points")

            if updated_fields:
                with transaction.atomic():
                    user.save(update_fields=updated_fields)

            context.update({
                "prompt_text": user_message,
                "prompt_rate": rate,
                "improvement_hint": improvement_hint,
                "refined_prompt": refined_prompt,
            })

    return render(request, "prompt_gamified/prompt_trainer.html", context)

@login_required
def leaderboard_view(request):
    users_list = CustomUser.objects.filter(is_active=True).order_by('-exp')
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    start_rank = (page_obj.number - 1) * paginator.per_page
    for idx, user in enumerate(page_obj.object_list, start=1):
        user.rank_position = start_rank + idx
    context = {
        'page_obj': page_obj,
        'total_users': paginator.count,
    }
    return render(request, "prompt_gamified/leader_board.html", context)