# anon_support_manager/models.py

from django.db import models
from django.utils import timezone

class User(models.Model):
    user_id = models.BigIntegerField(unique=True)  # Уникальный идентификатор пользователя
    username = models.CharField(max_length=255)

    def __str__(self):
        return self.username


class Operator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='operator')  # Связь с пользователем
    is_active = models.BooleanField(default=False)  # Статус активности на смене

    def __str__(self):
        return f'Operator: {self.user.username} (Active: {self.is_active})'


class Ticket(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')  # Связь с пользователем
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')  # Связь с оператором
    question = models.TextField(blank=True, null=True)  # Вопрос пользователя
    status = models.CharField(max_length=50, choices=[('new', 'New'), ('in_progress', 'In Progress'), ('closed', 'Closed')], default='new')  # Статусы тикета
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления тикета

    def __str__(self):
        return f'Ticket #{self.ticket_id} - User: {self.user.username if self.user else "Unknown"}'
