from django.contrib import admin
from .models import BotUser

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_id', 'subscription_type', 'generated_links', 'is_blocked')
    search_fields = ('username', 'user_id')
    list_filter = ('subscription_type', 'is_blocked')