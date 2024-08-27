from django.shortcuts import render, redirect
from .models import File, BotUser
from .forms import UniqueKeyForm
from django.utils import timezone
from django.db.models import Sum  # Импортируем Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from cryptography.fernet import Fernet
from django.urls import reverse
import base64
from django.core.files.base import ContentFile
import os
import requests
from django.conf import settings
from datetime import timedelta


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        print(request.POST)  # Это выведет все ключи и значения POST-запроса в консоль
        try:
            # Получаем данные из POST-запроса
            unique_key = request.POST['key']
            file = request.FILES.get('file')  # Получаем файл из запроса
            lifetime = request.POST['lifetime']
            encryption_key = request.POST['encryption_key']
            file_type = request.POST.get('type', 'file')  # Тип файла
            text = request.POST.get('text', '')  # Текст, если он есть
            chat_id = request.POST.get('chat_id')  # Получаем chat_id из запроса

            if not file:
                return JsonResponse({'error': 'Файл не был загружен.'}, status=400)

            # Создаем объект File
            new_file = File.objects.create(
                unique_key=unique_key,
                file=file,
                encryption_key=encryption_key,
                type=file_type,
                text=text if file_type == 'image_text' else None,  # Добавляем текст, только если тип image_text
                chat_id=chat_id  # Сохраняем chat_id
            )

            # Генерируем URL для доступа к файлу
            file_url = request.build_absolute_uri(reverse('download_file', args=[unique_key]))

            return JsonResponse({
                'message': 'File uploaded successfully!',
                'file_id': new_file.id,
                'file_url': file_url,
                'unique_key': unique_key
            })
        
        except KeyError as e:
            # Обработка случая, когда одно из полей отсутствует
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

def delete_file(file_record):
    file_path = file_record.file.path
    file_record.delete()  # Удаляем запись из базы данных
    if os.path.exists(file_path):
        os.remove(file_path)  # Удаляем сам файл

# Функция для расшифровки файла
def decrypt_file(encrypted_data, key):
    try:
        # Декодируем ключ в байты
        fernet = Fernet(key.encode())  
        return fernet.decrypt(encrypted_data)
    except Exception as e:
        # Если произошла ошибка, возвращаем None
        return None

# Вьюха для загрузки файла по уникальному ключу
def download_file(request, key):
    try:
        file_record = File.objects.get(unique_key=key)
    except File.DoesNotExist:
        return HttpResponse("Такого файла не найдено", status=404)

    with file_record.file.open('rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)

    if decrypted_data is None:
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)

    # Обработка изображений
    if file_record.type in ['image', 'image_text']:
        image_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'image_data': image_base64,
            'is_image': True,
        })
    # Обработка видео
    elif file_record.type == 'video':
        video_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'video_data': video_base64,
            'is_video': True,
        })
    # Обработка других типов файлов
    else:
        file_content = ContentFile(decrypted_data)
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'file_content': file_content,
            'is_image': False,
        })
    

def file_view(request):
    error_message = None  # Инициализируем сообщение об ошибке
    image_data = None
    video_data = None
    file_url = None

    if request.method == 'POST':
        form = UniqueKeyForm(request.POST)
        if form.is_valid():
            unique_key = form.cleaned_data['unique_key']
            try:
                # Попробуем найти файл по ключу
                file_record = File.objects.get(unique_key=unique_key)

                # Дешифровываем данные файла
                with file_record.file.open('rb') as f:
                    encrypted_data = f.read()

                decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)

                if decrypted_data is None:
                    error_message = "Не удалось расшифровать файл. Проверьте ключ шифрования."
                else:
                    # Если это изображение, конвертируем в base64 для отображения
                    if file_record.type in ['image', 'image_text']:
                        image_data = base64.b64encode(decrypted_data).decode('utf-8')
                    # Если это видео, конвертируем в base64 для отображения
                    elif file_record.type == 'video':
                        video_data = base64.b64encode(decrypted_data).decode('utf-8')
                    else:
                        # Если это другой тип файла, сохраняем его для передачи в шаблон
                        file_url = file_record.file.url

                    # Удаляем файл после отправки уведомления
                    file_path = file_record.file.path
                    file_record.delete()  # Удаляем запись из базы данных
                    
                    # Проверяем существование файла перед удалением
                    if os.path.exists(file_path):
                        os.remove(file_path)  # Удаляем сам файл

                    return render(request, 'file_detail.html', {
                        'file': file_record,
                        'image_data': image_data,
                        'video_data': video_data,
                        'file_url': file_url,
                    })
                        
            except Exception:
                error_message = "Такого файла не существует."  # Общее сообщение об ошибке

    else:
        form = UniqueKeyForm()

    return render(request, 'file_view.html', {
        'form': form,
        'error_message': error_message,  # Передаём сообщение об ошибке в шаблон
    })


def send_broadcast(message, image_path=None):
    users = BotUser.objects.filter(is_blocked=False)  # Получаем список пользователей
    bot_token = settings.BOT_TOKEN  # Получаем токен из настроек

    for user in users:
        data = {'chat_id': user.user_id, 'caption': message}
        
        if image_path:
            # Отправка сообщения с изображением
            with open(image_path, 'rb') as image_file:
                files = {'photo': image_file}
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendPhoto', data=data, files=files)
        else:
            # Отправка только текста
            data = {'chat_id': user.user_id, 'text': message}
            requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data=data)

def bot_admin_panel(request):
    users = BotUser.objects.using('users_db').all()
    return render(request, 'bot_admin_panel.html', {'users': users})


def broadcast_view(request):
    if request.method == 'POST':
        message = request.POST.get('message')  # Получаем сообщение
        image = request.FILES.get('image')  # Получаем изображение, если есть

        # Если есть изображение, сохраняем его
        image_path = None
        if image:
            image_name = default_storage.save(os.path.join('uploads', image.name), image)
            image_path = os.path.join(settings.MEDIA_ROOT, image_name)

        # Отправляем рассылку
        send_broadcast(message, image_path)

        return render(request, 'bot_admin_panel.html', {'section': 'broadcast', 'status': 'Рассылка выполнена успешно!'})

    return render(request, 'bot_admin_panel.html', {'section': 'broadcast'})


def manage_users_view(request):
    users = BotUser.objects.all()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        try:
            user = BotUser.objects.get(user_id=user_id)

            if action == 'make_admin':
                user.is_admin = True
                user.save()
            elif action == 'remove_admin':
                user.is_admin = False
                user.save()
            elif action == 'add_subscription':
                user.subscription_type = 'PAID'  # Или другой тип подписки
                user.save()
            elif action == 'remove':
                user.subscription_type = 'FREE'  # Удалить подписку
                user.save()
            elif action == 'block':
                user.is_blocked = True
                user.save()
            elif action == 'unblock':
                user.is_blocked = False
                user.save()

            return redirect('manage_users')  # Переход на тот же раздел

        except BotUser.DoesNotExist:
            # Обработка ошибки, если пользователь не найден
            pass

    return render(request, 'bot_admin_panel.html', {'section': 'manage_users', 'users': users})


def get_statistics():
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)

    # Данные для графиков
    new_subscribers_data = []
    premium_users_data = []
    link_data = []

    for day in range(30):
        date = today - timedelta(days=day)
        
        # Получаем количество новых подписчиков за день
        new_subscribers_count = BotUser.objects.filter(join_date__date=date).count()
        new_premium_count = BotUser.objects.filter(join_date__date=date, subscription_type='PAID').count()
        
        # Получаем количество сгенерированных ссылок за день
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

def statistics_view(request):
    statistics = get_statistics()
    return render(request, 'bot_admin_panel.html', {'section': 'statistics', 'statistics': statistics})
