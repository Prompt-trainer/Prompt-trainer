from django.shortcuts import render
from django.contrib.auth.decorators import login_required
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