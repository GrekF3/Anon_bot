from django.shortcuts import render, redirect
from .models import BotUser
import requests
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.files.storage import default_storage
import os
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

def send_broadcast(message, image_path=None):
    users = BotUser.objects.all()
    bot_token = settings.ANON_TOKEN

    for user in users:
        data = {
            'chat_id': user.user_id,
            'text': message,
            'parse_mode': 'Markdown'  # Использование Markdown для форматирования
        }

        if image_path:
            with open(image_path, 'rb') as image_file:
                files = {'photo': image_file}
                data['caption'] = message  # Markdown будет применяться к `caption`
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendPhoto', data=data, files=files)
        else:
            requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data=data)


@login_required
def bot_admin_panel(request):
    return render(request, 'bot_admin_panel.html', {'section': 'manage_users', 'users': BotUser.objects.all()})

@login_required
def broadcast_view(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        image = request.FILES.get('image')

        image_path = None
        if image:
            image_name = default_storage.save(os.path.join('uploads', image.name), image)
            image_path = os.path.join(settings.MEDIA_ROOT, image_name)
        send_broadcast(message, image_path)
        return render(request, 'bot_admin_panel.html', {'section': 'broadcast', 'status': 'Рассылка выполнена успешно!'})

    return render(request, 'bot_admin_panel.html', {'section': 'broadcast'})

@login_required
def manage_users_view(request):
    users = BotUser.objects.all()

    # Возвращаем страницу управления пользователями с отображением всех пользователей
    return render(request, 'bot_admin_panel.html', {
        'section': 'manage_users',
        'users': users,
        'total_users': users.count(),  # Отображаем общее количество пользователей
    })
