from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import get_user_model
from .ai_func import evaluate_prompt_quality
from django.http import JsonResponse
from .models import Prompt

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
            rate, improvement_hint, refined_prompt = evaluate_prompt_quality(user_message)

            Prompt.objects.create(
                prompt_text=user_message,
                improvement_hint=improvement_hint,
                rate=rate,
                user=request.user,
            )

            context.update({
                "prompt_text": user_message,
                "prompt_rate": rate,
                "improvement_hint": improvement_hint,
                "refined_prompt": refined_prompt,
            })

    return render(request, "prompt_gamified/prompt_trainer.html", context)