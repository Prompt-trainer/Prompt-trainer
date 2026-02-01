from django.urls import path

from prompt_gamified.api_views import GoogleCallbackView, GoogleLoginView
from . import views

app_name = "prompt_gamified"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("home", views.home_view, name="home_page"),
    path("auth/google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("auth/google/callback/", GoogleCallbackView.as_view(), name="google_callback"),
]
