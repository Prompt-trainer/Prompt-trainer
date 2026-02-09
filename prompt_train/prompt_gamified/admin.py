from django.contrib import admin
from .models import Prompt


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('user', 'prompt_text_preview', 'rate', 'improvement_hint_preview')
    list_filter = ('rate', 'user')
    search_fields = ('prompt_text', 'improvement_hint', 'user__nickname')
    list_editable = ('rate',)
    
    def prompt_text_preview(self, obj):
        return obj.prompt_text[:50] + '...' if len(obj.prompt_text) > 50 else obj.prompt_text
    prompt_text_preview.short_description = 'Текст промпту'
    
    def improvement_hint_preview(self, obj):
        return obj.improvement_hint[:40] + '...' if len(obj.improvement_hint) > 40 else obj.improvement_hint
    improvement_hint_preview.short_description = 'Підказка'