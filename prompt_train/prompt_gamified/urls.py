from django.urls import path
from . import views

app_name = "prompt_gamified"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("home", views.home_view, name="home_page"),
]
