# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from .models import Ticket, User, Operator, Message
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
import logging
import requests
from django.conf import settings
import os

logger = logging.getLogger(__name__)
@login_required
def support_panel_view(request):
    print("support_panel_view called")
    
    # Получение всех тикетов и операторов
    open_tickets = Ticket.objects.filter(status='new').order_by('-created_at')  # Открытые тикеты
    in_progress_tickets = Ticket.objects.filter(status='in_progress').order_by('-created_at')  # Тикеты в работе
    closed_tickets = Ticket.objects.filter(status='closed').order_by('-created_at')  # Закрытые тикеты

    operators = Operator.objects.all()
    
    if request.method == 'POST':
        print("Received POST request for ticket management")
        ticket_id = request.POST.get('ticket_id')
        action = request.POST.get('action')

        # Обработка действия
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
            if action == 'close':
                ticket.status = 'closed'
                ticket.save()
                messages.success(request, f"Тикет #{ticket_id} закрыт успешно.")
                print(f"Ticket #{ticket_id} closed successfully")
            elif action == 'assign':
                assigned_user_id = request.POST.get('assigned_user')
                assigned_user = User.objects.get(user_id=assigned_user_id)
                ticket.assigned_user = assigned_user
                ticket.status = 'in_progress'
                ticket.save()
                messages.success(request, f"Тикет #{ticket_id} назначен оператору {assigned_user.username}.")
                print(f"Ticket #{ticket_id} assigned to {assigned_user.username}")
        except Ticket.DoesNotExist:
            messages.error(request, f"Тикет #{ticket_id} не найден.")
            print(f"Ticket #{ticket_id} not found")
        except User.DoesNotExist:
            messages.error(request, f"Оператор с ID {assigned_user_id} не найден.")
            print(f"User with ID {assigned_user_id} not found")
        except Exception as e:
            messages.error(request, f"Произошла ошибка: {str(e)}")
            print(f"Error: {str(e)}")

    return render(request, 'bot_admin_panel.html', {
        'section':'support_panel',
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'closed_tickets': closed_tickets,
        'operators': operators,
    })


def send_telegram_message(message, user_id):
    """Отправляет сообщение в Telegram."""
    url = f"https://api.telegram.org/bot{settings.ANON_SUPPORT_TOKEN}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': message,
        'parse_mode': 'Markdown'  # Можно использовать 'Markdown' или 'HTML' в зависимости от ваших потребностей
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Поднимает исключение для статусов 4xx и 5xx
        logger.info(f"Message sent to Telegram: {message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")


# Чат с пользователем по тикету
@login_required
def ticket_chat(request, ticket_id):
    logger.debug(f"Accessing ticket_chat for ticket_id: {ticket_id}")

    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    logger.debug(f"Retrieved ticket: {ticket}")

    messages = ticket.messages.all()  # Получаем все сообщения, связанные с тикетом
    logger.debug(f"Messages for ticket {ticket_id}: {messages.count()} found")

    if request.method == 'POST':
        message_content = request.POST.get('message')
        logger.debug(f"Received POST request with message content: {message_content}")

        if message_content:
            try:
                user_id = ticket.user.user_id
                ticket.add_message(sender=ticket.assigned_user, text=message_content)
                logger.info(f"Message added for ticket {ticket_id} by user")
                response = send_telegram_message(
                    message=message_content,
                    user_id=user_id,
                )
                return redirect('ticket_chat', ticket_id=ticket.ticket_id)  # Обновляем страницу
            except Exception as e:
                logger.error(f"Error adding message for ticket {ticket_id}: {e}")
                # Возможно, вы захотите добавить сообщение об ошибке для пользователя

    context = {
        'ticket': ticket,
        'chat_messages': messages
    }
    logger.debug(f"Rendering chat for ticket_id: {ticket_id}")
    return render(request, 'support/chat.html', context=context)