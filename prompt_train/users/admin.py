from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'nickname', 'rank', 'points', 'exp', 'is_staff', 'is_active')
    list_filter = ('rank', 'is_staff', 'is_active')
    search_fields = ('email', 'nickname')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Особиста інформація', {'fields': ('nickname',)}),
        ('Гейміфікація', {'fields': ('rank', 'points', 'exp')}),
        ('Права доступу', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )
