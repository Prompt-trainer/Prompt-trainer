from django.urls import path
from . import views
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)


app_name = 'auth'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path('logout/', LogoutView.as_view(next_page='auth:login'), name='logout'),
]
