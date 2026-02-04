from django.urls import path

from prompt_gamified.api_views import GoogleCallbackView, GoogleLoginView
from . import views



app_name = "prompt_gamified"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("home", views.home_view, name="home_page"),
    path("auth/google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("auth/google/callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("good-prompts/", views.good_prompts_view, name="good_prompts"),
    path("prompt-trainer/", views.prompt_trainer_view, name="prompt_trainer"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
]
