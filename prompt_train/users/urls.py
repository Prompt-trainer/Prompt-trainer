from django.urls import path
from . import views
from prompt_gamified.api_views import GoogleLoginView, GoogleCallbackView
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView, 
    PasswordChangeDoneView
)
from django.urls import reverse_lazy

app_name = "auth"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="auth:login"), name="logout"),
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("password/change/",PasswordChangeView.as_view(
            template_name="users/password_change.html",
            success_url=reverse_lazy("auth:password_change_done")),
            name="password_change"),
    path("password/change/done/",PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"),name="password_change_done"
    ),
    path("profile/delete/", views.delete_profile_view, name="delete_profile"),
]
