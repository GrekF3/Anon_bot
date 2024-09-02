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

@login_required
def send_broadcast(message, image_path=None):
    print("send_broadcast called")
    users = BotUser.objects.filter(is_blocked=False)
    bot_token = settings.ANON_TOKEN

    for user in users:
        print("Sending message to user:", user.user_id)
        data = {'chat_id': user.user_id, 'caption': message}
        
        if image_path:
            print("Sending image with message")
            with open(image_path, 'rb') as image_file:
                files = {'photo': image_file}
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendPhoto', data=data, files=files)
        else:
            print("Sending text message only")
            data = {'chat_id': user.user_id, 'text': message}
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

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        try:
            user = BotUser.objects.get(user_id=user_id)

            if action == 'add_subscription':
                user.subscription_type = 'PAID'
                user.save()
            elif action == 'remove':
                user.subscription_type = 'FREE'
                user.save()
            elif action == 'block':
                user.is_blocked = True
                user.save()
            elif action == 'unblock':
                user.is_blocked = False
                user.save()

            return redirect('manage_users')

        except BotUser.DoesNotExist:
            pass

    return render(request, 'bot_admin_panel.html', {'section': 'manage_users', 'users': users})

@login_required
def get_statistics(request):
    print("get_statistics called")
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)

    new_subscribers_data = []
    premium_users_data = []
    link_data = []

    for day in range(30):
        date = today - timedelta(days=day)
        
        new_subscribers_count = BotUser.objects.filter(join_date__date=date).count()
        new_premium_count = BotUser.objects.filter(join_date__date=date, subscription_type='PAID').count()
        link_count = BotUser.objects.filter(join_date__date=date).aggregate(Sum('generated_links'))['generated_links__sum'] or 0

        new_subscribers_data.append(new_subscribers_count)
        premium_users_data.append(new_premium_count)
        link_data.append(link_count)

    return {
        'user_count': BotUser.objects.count(),
        'link_count': BotUser.objects.aggregate(Sum('generated_links'))['generated_links__sum'] or 0,
        'premium_count': BotUser.objects.filter(subscription_type='PREMIUM').count(),
        'new_subscribers_data': new_subscribers_data,
        'premium_users_data': premium_users_data,
        'link_data': link_data,
        'labels': [(today - timedelta(days=day)).strftime('%Y-%m-%d') for day in range(30)],
    }

@login_required
def statistics_view(request):
    statistics = get_statistics(request)
    return render(request, 'bot_admin_panel.html', {'section': 'statistics', 'statistics': statistics})

