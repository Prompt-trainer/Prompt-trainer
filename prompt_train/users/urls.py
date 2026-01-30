from django.urls import path
from . import views
from prompt_gamified.api_views import GoogleLoginView, GoogleCallbackView
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)

app_name = "auth"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="auth:login"), name="logout"),
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google_callback")
]
