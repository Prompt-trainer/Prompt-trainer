from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index_view(request):
    return render(request, "prompt_gamified/index.html")


@login_required
def home_view(request):
    return render(request, "prompt_gamified/home.html")
