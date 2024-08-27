from django.contrib import admin
from .models import File, BotUser

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('unique_key', 'file', 'created_at')
    search_fields = ('unique_key',)

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_id', 'subscription_type', 'generated_links', 'is_admin', 'is_blocked')
    search_fields = ('username', 'user_id')
    list_filter = ('subscription_type', 'is_admin', 'is_blocked')