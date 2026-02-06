from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_room, name='global_chat'),  
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('private/<int:user_id>/', views.private_chat, name='private_chat'),
    path('users/', views.users_list, name='users_list'),
]
