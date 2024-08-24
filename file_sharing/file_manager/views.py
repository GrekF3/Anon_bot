from django.shortcuts import render, redirect
from .models import File
from .forms import UniqueKeyForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from cryptography.fernet import Fernet
from django.urls import reverse
import base64
from django.core.files.base import ContentFile
import os

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