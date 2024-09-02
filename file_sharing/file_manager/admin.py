from django.contrib import admin
from .models import File

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('unique_key', 'file', 'created_at')
    search_fields = ('unique_key',)
