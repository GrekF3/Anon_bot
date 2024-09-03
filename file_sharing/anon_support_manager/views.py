# views.py

from django.shortcuts import render, redirect
from .models import Ticket, User, Operator
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
