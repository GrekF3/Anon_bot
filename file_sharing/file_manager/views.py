from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import File
from .forms import UniqueKeyForm, UploadFileForm
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import os
import json
import mimetypes
import uuid, base64
from cryptography.fernet import Fernet

# Вспомогательная функция для удаления файла
def delete_file(file_record):
    file_path = file_record.file.path
    file_record.delete()
    if os.path.exists(file_path):
        os.remove(file_path)

@csrf_exempt
def upload_file(request):
    import time
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        unique_key = request.POST.get('key')
        file_type = request.POST.get('type')
        text = request.POST.get('text', '')
        mime_type = request.POST.get('mime_type')
                
        if uploaded_file and unique_key and file_type:
            try:
                # Чтение содержимого файла
                file_data = uploaded_file.read()
                print(f"Прочитанные данные файла (размер: {len(file_data)} байт)")

                # Генерация ключа шифрования
                encryption_key = Fernet.generate_key().decode()
                print(f"Сгенерированный ключ шифрования: {encryption_key}")

                # Шифрование файла
                fernet = Fernet(encryption_key.encode())
                encrypted_file_data = fernet.encrypt(file_data)
                print(f"Зашифрованные данные файла (размер: {len(encrypted_file_data)} байт)")

                # Создание файла в памяти с зашифрованными данными
                encrypted_file_content = ContentFile(encrypted_file_data, name=uploaded_file.name)

                # Определение MIME-типа
                if not mime_type:
                    mime_type = 'application/octet-stream'

                print(f"Определённый MIME-тип: {mime_type}")

                # Создание записи в базе данных
                file_record = File.objects.create(
                    unique_key=unique_key,
                    file=encrypted_file_content,
                    encryption_key=encryption_key,  # Сохраняем ключ шифрования
                    type=file_type,
                    text=text,
                    mime_type=mime_type  # Сохраняем MIME-тип
                )

                # Создание полного URL для файла
                file_url = request.build_absolute_uri(reverse('file_view', args=[unique_key]))

                # Формирование ответа
                response_data = {
                    'file_url': file_url,
                    'unique_key': unique_key,
                }
                print(f"Файл успешно загружен. URL: {file_url}")
                return JsonResponse(response_data, status=200)

            except Exception as e:
                print(f"Ошибка при обработке файла: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
        
        return JsonResponse({'error': 'Missing required fields'}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def handle_file_upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        unique_key = str(uuid.uuid4())  # Генерация уникального ключа
        text = request.POST.get('text', '')
        mime_type = request.POST.get('mime_type', 'application/octet-stream')

        if uploaded_file:
            try:
                # Чтение содержимого файла
                file_data = uploaded_file.read()
                print(f"Прочитанные данные файла (размер: {len(file_data)} байт)")

                # Генерация ключа шифрования
                encryption_key = Fernet.generate_key().decode()
                print(f"Сгенерированный ключ шифрования: {encryption_key}")

                # Шифрование файла
                fernet = Fernet(encryption_key.encode())
                encrypted_file_data = fernet.encrypt(file_data)

                # Создание файла в памяти с зашифрованными данными
                encrypted_file_content = ContentFile(encrypted_file_data, name=uploaded_file.name)

                # Определение типа файла (изображение, видео или обычный файл)
                mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                if mime_type and mime_type.startswith('image'):
                    file_type = 'image'
                elif mime_type and mime_type.startswith('video'):
                    file_type = 'video'
                else:
                    file_type = 'file'

                # Создание записи в базе данных
                File.objects.create(
                    unique_key=unique_key,
                    file=encrypted_file_content,
                    encryption_key=encryption_key,
                    type=file_type,
                    text=text,
                    mime_type=mime_type
                )

                print(f"Файл успешно загружен с уникальным ключом: {unique_key}")

                # Формируем ссылку на файл (или замените на нужный URL)
                link = request.build_absolute_uri(reverse('file_view', args=[unique_key]))

                # Редирект на страницу успеха с параметрами
                return HttpResponseRedirect(reverse('upload_success') + f"?unique_key={unique_key}&link={link}")

            except Exception as e:
                print(f"Ошибка при обработке файла: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
        
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)



def home(request):
    error_message = None
    error_file_message = None
    upload_form = UploadFileForm()
    search_form = UniqueKeyForm()

    if request.method == 'POST':
        if 'unique_key' in request.POST:  # Обработка поиска файла по ключу
            search_form = UniqueKeyForm(request.POST)
            if search_form.is_valid():
                unique_key = search_form.cleaned_data['unique_key']
                try:
                    file_record = File.objects.get(unique_key=unique_key)
                    return redirect('file_view', key=unique_key)
                except File.DoesNotExist:
                    error_message = "Файл с таким ключом не найден."
            else:
                error_message = "Некорректный ключ."
        elif 'file' in request.FILES:  # Обработка загрузки файла
            # Перенаправление на новую функцию для загрузки файла
            return handle_file_upload(request)

    context = {
        'form': search_form,
        'file_form': upload_form,
        'error_message': error_message,
        'error_file_message': error_file_message,
    }

    return render(request, 'home.html', context)
# Представление для отображения и скачивания файла
def file_view(request, key):
    try:
        file_record = File.objects.get(unique_key=key)
    except File.DoesNotExist:
        return HttpResponse("Такого файла не найдено", status=404)

    with file_record.file.open('rb') as f:
        encrypted_data = f.read()

    # Расшифровка данных
    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)
    
    if decrypted_data is None:
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)

    mime_type, _ = mimetypes.guess_type(file_record.file.name)

    # Получение информации о файле
    file_size = len(decrypted_data)  # Размер файла в байтах
    upload_date = file_record.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Дата загрузки

    # Подготовка контекста для передачи в шаблон
    context = {
        'file': file_record,
        'file_size': file_size,
        'upload_date': upload_date,
        'mime_type': mime_type,
    }

    if file_record.type == 'image':
        image_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        context['image_data'] = image_base64
        context['is_image'] = True
        return render(request, 'file_detail.html', context)
    
    elif file_record.type == 'video':
        video_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        context['video_data'] = video_base64
        context['is_video'] = True
        return render(request, 'file_detail.html', context)

    elif file_record.type == 'file':
        # Здесь мы возвращаем информацию о файле, если это обычный файл
        return render(request, 'file_detail.html', {
            'file': file_record,
            'file_size': file_size,
            'upload_date': upload_date,
            'mime_type': mime_type,
            'is_file': True,
        })

    # Если не подходит под предыдущие условия, просто возвращаем файл как загрузку
    response = HttpResponse(decrypted_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_record.file.name}"'
    return response

# Представление для успешной загрузки
def upload_success_view(request):
    unique_key = request.GET.get('unique_key')
    link = request.GET.get('link')
    if not unique_key or not link:
        return HttpResponseRedirect(reverse('home'))
    return render(request, 'upload_success.html', {'unique_key': unique_key, 'link': link})

# Представление для удаления файла после закрытия страницы
@csrf_exempt
def delete_file_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        key = data.get('key')
        try:
            file_record = File.objects.get(unique_key=key)
            delete_file(file_record)
            return JsonResponse({'status': 'success'})
        except File.DoesNotExist:
            return JsonResponse({'status': 'file_not_found'}, status=404)
    return JsonResponse({'status': 'invalid_method'}, status=405)

def decrypt_file(encrypted_data, key):
    try:
        fernet = Fernet(key.encode())  # Создание объекта Fernet с ключом
        decrypted_data = fernet.decrypt(encrypted_data)  # Дешифрование данных
        return decrypted_data
    except Exception as e:
        print("Error during file decryption:", e)  # Логирование ошибок
        return None

def download_file(request, key):
    # Получение записи файла по уникальному ключу
    file_record = get_object_or_404(File, unique_key=key)
    print(f"Получена запись файла: {file_record}")

    with file_record.file.open('rb') as f:
        encrypted_data = f.read()  # Чтение зашифрованных данных
        print(f"Прочитаны зашифрованные данные, размер: {len(encrypted_data)} байт")

    # Расшифровка данных
    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)
    if decrypted_data is None:
        print("Ошибка: Не удалось расшифровать файл.")
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)
    print("Данные расшифрованы.")

    # Определение MIME-типа
    mime_type = file_record.mime_type or mimetypes.guess_type(file_record.file.name)[0]
    if not mime_type:
        mime_type = 'application/octet-stream'
    print(f"Определённый MIME-тип: {mime_type}")

    # Получаем расширение файла и имя файла
    original_filename = file_record.file.name
    file_name, file_extension = os.path.splitext(original_filename)
    if not file_extension:
        file_extension = mimetypes.guess_extension(mime_type) or '.bin'
    print(f"Определённое расширение файла: {file_extension}")

    filename = f"{file_record.unique_key}{file_extension}"  # Задаем имя файла с расширением
    print(f"Имя файла для скачивания: {filename}")

    # Формирование ответа с расшифрованными данными
    response = HttpResponse(decrypted_data, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    print("Файл готов к отправке.")
    delete_file(file_record)
    print(f"Файл {file_record.file.name} был удалён после скачивания.")

    return response