from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import CustomUser, Cosmetic, UserCosmetic


class UserCosmeticInline(TabularInline):
    model = UserCosmetic
    extra = 0
    readonly_fields = ("purchase_date",)
    fields = ("cosmetic", "purchase_date")
    show_change_link = True


@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin, UserAdmin):
    list_display = (
        "email",
        "nickname",
        "rank",
        "points",
        "exp",
        "is_staff",
        "is_active",
    )
    list_filter = ("rank", "is_staff", "is_active")
    search_fields = ("email", "nickname")
    ordering = ("email",)
    inlines = [UserCosmeticInline]
    warn_unsaved_changes = True

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("nickname", "profile_picture")}),
        (
            "Gamification",
            {
                "fields": (
                    "rank",
                    "points",
                    "exp",
                    "active_ring",
                    "active_element",
                    "active_title",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nickname",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(Cosmetic)
class CosmeticAdmin(ModelAdmin):
    list_display = ("name", "type", "price", "rank_required")
    list_filter = ("type", "rank_required")
    search_fields = ("name",)
    list_editable = ("price",)
    warn_unsaved_changes = True


@admin.register(UserCosmetic)
class UserCosmeticAdmin(ModelAdmin):
    list_display = ("user", "cosmetic", "purchase_date")
    list_filter = ("cosmetic__type",)
    search_fields = ("user__nickname", "user__email", "cosmetic__name")
    readonly_fields = ("purchase_date",)
