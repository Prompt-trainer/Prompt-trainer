from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_participants", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("participants__nickname", "participants__email")
    filter_horizontal = ("participants",)

    def get_participants(self, obj):
        return ", ".join([user.nickname for user in obj.participants.all()])

    get_participants.short_description = "Учасники"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "conversation",
        "get_content_preview",
        "timestamp",
        "is_edited",
        "is_read",
    )
    list_filter = ("timestamp", "is_edited", "is_read")
    search_fields = ("user__nickname", "user__email")
    readonly_fields = ("timestamp", "edited_at", "get_decrypted_message")

    def get_content_preview(self, obj):
        content = obj.get_decrypted_content()
        return content[:50] + "..." if len(content) > 50 else content

    get_content_preview.short_description = "Зміст"

    def get_decrypted_message(self, obj):
        return obj.get_decrypted_content()

    get_decrypted_message.short_description = "Повідомлення (розшифроване)"
