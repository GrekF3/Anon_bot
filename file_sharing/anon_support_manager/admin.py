from django.contrib import admin
from .models import User, Ticket, Operator

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username')  # Убрали is_operator
    search_fields = ('username', 'user_id')  # Поля для поиска

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'get_assigned_user_username', 'status')  # Изменено на get_assigned_user_username
    search_fields = ('ticket_id', 'user__username', 'assigned_user__username')  # Изменено на assigned_user
    list_filter = ('status',)  # Фильтр по статусу
    raw_id_fields = ('user',)  # Поле пользователя отображается как поле с выбором ID

    def get_assigned_user_username(self, obj):
        return obj.assigned_user.username if obj.assigned_user else 'Нет оператора'
    get_assigned_user_username.short_description = 'Оператор'  # Заголовок для колонки

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active')  # Отображение информации о операторе
