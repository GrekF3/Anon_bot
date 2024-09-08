# -------Django
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf.urls import handler404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
# -------MODELS
from .models import File, AdsBanner
from .forms import UniqueKeyForm, UploadFileForm

# -------LOGICAL BASE
import os
import mimetypes
import uuid, base64
from cryptography.fernet import Fernet
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Вспомогательная функция для удаления файла
def delete_file(file_record):
    file_path = file_record.file.path
    file_record.delete()
    if os.path.exists(file_path):
        os.remove(file_path)

def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        unique_key = request.POST.get('key')
        file_type = request.POST.get('type')
        text = request.POST.get('text', '')
        mime_type = request.POST.get('mime_type')
        expiry_duration = request.POST.get('expiry_duration')  # Получаем срок жизни файла из запроса

        if uploaded_file and unique_key and file_type:
            try:
                # Чтение содержимого файла
                file_data = uploaded_file.read()
                # Генерация ключа шифрования
                encryption_key = Fernet.generate_key().decode()

                # Шифрование файла
                fernet = Fernet(encryption_key.encode())
                encrypted_file_data = fernet.encrypt(file_data)

                # Создание файла в памяти с зашифрованными данными
                encrypted_file_content = ContentFile(encrypted_file_data, name=uploaded_file.name)

                # Определение MIME-типа
                if not mime_type:
                    mime_type = 'application/octet-stream'

                # Создание записи в базе данных
                file_record = File.objects.create(
                    unique_key=unique_key,
                    file=encrypted_file_content,
                    encryption_key=encryption_key,  # Сохраняем ключ шифрования
                    type=file_type,
                    text=text,
                    mime_type=mime_type  # Сохраняем MIME-тип
                )

                # Установка срока жизни файла, если он указан
                if expiry_duration != 'one_time':
                    try:
                        expiry_duration, _ = str(expiry_duration).split('_')
                        expiry_duration = int(expiry_duration)
                        file_record.set_expiry(expiry_duration)
                    except ValueError:
                        logger.warning("Ошибка: Неверный формат срока жизни файла")

                # Создание полного URL для файла
                file_url = request.build_absolute_uri(reverse('file_view', args=[unique_key]))

                # Логирование успешной загрузки файла
                logger.info(f"Файл успешно загружен. URL: {file_url}, уникальный ключ: {unique_key}, тип файла: {file_type}, MIME-тип: {mime_type}")

                # Формирование ответа
                response_data = {
                    'file_url': file_url,
                    'unique_key': unique_key,
                }
                return JsonResponse(response_data, status=200)

            except Exception as e:
                logger.error(f"Ошибка при обработке файла: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)

        logger.error("Ошибка: отсутствуют обязательные поля")
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    logger.error("Ошибка: недопустимый метод")
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def handle_file_upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        unique_key = str(uuid.uuid4())  # Генерация уникального ключа
        text = request.POST.get('text', '')
        mime_type = request.POST.get('mime_type', 'application/octet-stream')
        expiry_duration = request.POST.get('file_lifetime') 

        if uploaded_file:
            try:
                # Чтение содержимого файла
                file_data = uploaded_file.read()
                logger.info(f"Прочитанные данные файла (размер: {len(file_data)} байт)")

                # Генерация ключа шифрования
                encryption_key = Fernet.generate_key().decode()
                logger.info(f"Сгенерированный ключ шифрования: {encryption_key}")

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
                elif mime_type and mime_type.startswith('audio'):
                    file_type = 'audio'
                else:
                    file_type = 'file'
                
                # Создание записи в базе данных
                file_record = File.objects.create(
                    unique_key=unique_key,
                    file=encrypted_file_content,
                    encryption_key=encryption_key,
                    type=file_type,
                    text=text,
                    mime_type=mime_type
                )

                # Логирование создания записи
                logger.info(f"Файл сохранен в базе данных: уникальный ключ: {unique_key}, тип файла: {file_type}, MIME-тип: {mime_type}")

                if expiry_duration == 'one_time':
                    expiration_str = 'Одноразовая ссылка'
                else:
                    try:
                        expiry_duration, _ = str(expiry_duration).split('_')
                        expiry_duration = int(expiry_duration)
                        file_record.set_expiry(expiry_duration)
                        logger.info(f"Срок жизни файла установлен: {expiry_duration} дней")
                        
                        # Определяем правильное склонение
                        if expiry_duration == 1:
                            expiration_str = "1 день"
                        elif 2 <= expiry_duration <= 4:
                            expiration_str = f"{expiry_duration} дня"
                        else:
                            expiration_str = f"{expiry_duration} дней"
                    except ValueError:
                        expiration_str = 'не задан'  # Установите значение по умолчанию при ошибке
                        logger.warning("Ошибка: Неверный формат срока жизни файла")

                # Сохранение информации в сессии
                request.session['upload_success'] = {
                    'unique_key': unique_key,
                    'link': request.build_absolute_uri(reverse('file_view', args=[unique_key])),
                    'file_expiration': expiration_str
                }

                # Логирование успешной загрузки
                logger.info(f"Файл успешно загружен. Уникальный ключ: {unique_key}, срок жизни: {expiration_str}")

                # Перенаправление на страницу успешной загрузки
                return HttpResponseRedirect(reverse('upload_success'))

            except Exception as e:
                logger.error(f"Ошибка при обработке файла: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
        
        logger.error("Ошибка: отсутствуют обязательные поля")
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    logger.error("Ошибка: недопустимый метод")
    return JsonResponse({'error': 'Invalid method'}, status=405)


def home(request, error_message=None):
    error_file_message = None
    upload_form = UploadFileForm()
    search_form = UniqueKeyForm()
    ads_banners = AdsBanner.objects.filter(is_active=True)

    if request.method == 'POST':
        if 'unique_key' in request.POST:  # Обработка поиска файла по ключу
            search_form = UniqueKeyForm(request.POST)
            if search_form.is_valid():
                unique_key = search_form.cleaned_data['unique_key']
                try:
                    return redirect('file_view', key=unique_key)
                except File.DoesNotExist:
                    error_message = "Файл с таким ключом не найден."
                    logger.error(error_message)
            else:
                error_message = "Некорректный ключ."
                logger.warning(error_message)
        elif 'file' in request.FILES:  # Обработка загрузки файла
            try:
                # Перенаправление на новую функцию для загрузки файла
                return handle_file_upload(request)
            except Exception as e:
                error_message = "Ошибка при загрузке файла."
                logger.error(f"{error_message} Подробности: {str(e)}")

    context = {
        'form': search_form,
        'file_form': upload_form,
        'error_message': error_message,
        'error_file_message': error_file_message,
        'ads_banners': ads_banners,
    }

    return render(request, 'home.html', context)

# Представление для отображения и скачивания файла
def file_view(request, key):
    error_message = None  # Инициализируем переменную для ошибки
    logger.info("Начало обработки запроса для ключа: %s", key)

    try:
        file_record = File.objects.get(unique_key=key)
        logger.info("Файл с ключом %s найден в базе данных", key)
    except File.DoesNotExist:
        # Сообщение об ошибке, если файла нет
        error_message = "Такого ключа не существует."
        logger.error(error_message)
        return home(request, error_message)
    
    # Проверка, доступен ли файл для скачивания
    if file_record.is_opened:
        logger.info("Файл уже открыт")
        # Если файл может быть загружен, но срок его действия истек
        if file_record.can_be_downloaded and (file_record.is_expired() or file_record.expires_at is None):
            logger.warning("Файл может быть загружен, но срок действия истек или нет даты истечения")
            # Удаляем файл, так как он уже был открыт или срок действия истек
            file_path = file_record.file.path
            file_record.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Файл %s был удален из файловой системы.", file_path)
            return HttpResponse("Файл недоступен для скачивания", status=403)
    # Если файл был открыт и срок действия истек (если он одноразовый)
    elif file_record.is_opened and file_record.is_expired():
        logger.warning("Файл был открыт и срок действия истек")
        # Удаляем файл
        file_path = file_record.file.path
        file_record.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Файл %s был удален из файловой системы.", file_path)
        return HttpResponse("Файл недоступен для скачивания", status=403)

    logger.info("Чтение файла")
    # Чтение файла
    try:
        with file_record.file.open('rb') as f:
            encrypted_data = f.read()
    except FileNotFoundError:
        error_message = "Ошибка: файл не найден."
        logger.error(error_message)
        return home(request, error_message)
    except IOError:
        error_message = "Ошибка: не удалось прочитать файл."
        logger.error(error_message)
        return home(request, error_message)
    except Exception as e:
        error_message = f"Произошла ошибка: {e}"
        logger.error(error_message)
        return home(request, error_message)

    logger.info("Файл прочитан, начинаем расшифровку")
    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)
    
    if decrypted_data is None:
        logger.error("Ошибка расшифровки файла")
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)

    mime_type = file_record.mime_type
    logger.info("MIME-тип файла: %s", mime_type)

    file_size = len(decrypted_data) / (1024 * 1024)  # Размер файла в МБ
    upload_date = file_record.created_at.strftime('%Y-%m-%d %H:%M:%S')
    logger.info("Размер файла: %.2f МБ, дата загрузки: %s", file_size, upload_date)
    
    context = {
        'file': file_record,
        'file_size': f"{file_size:.2f} МБ",
        'upload_date': upload_date,
        'mime_type': mime_type,
    }

    if file_record.type == 'image':
        logger.info("Файл является изображением")
        image_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        context['image_data'] = image_base64
        render_response = render(request, 'file_detail.html', context)

    elif file_record.type == 'video':
        logger.info("Файл является видео")
        video_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        context['video_data'] = video_base64
        render_response = render(request, 'file_detail.html', context)

    elif file_record.type == 'audio':
        logger.info("Файл является аудио")
        audio_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        context['audio_data'] = audio_base64
        render_response = render(request, 'file_detail.html', context)

    elif file_record.type == 'file':
        logger.info("Файл является простым файлом")
        render_response = render(request, 'file_detail.html', context)

    else:
        logger.warning("Файл неизвестного типа, отправляем как байтовый поток")
        render_response = HttpResponse(decrypted_data, content_type='application/octet-stream')
        render_response['Content-Disposition'] = f'attachment; filename="{file_record.file.name}"'

    # Помечаем файл как открытый и запускаем проверку удаления
    if not file_record.is_opened:
        link_opened(file_record)

    return render_response

def link_opened(file_record):
    """
    Помечает файл как открытый 
    """
    if not file_record.is_opened:
        file_record.mark_as_opened()  # Обновляем статус открытия

# Представление для успешной загрузки
def upload_success_view(request):
    upload_success = request.session.get('upload_success')
    
    # Проверка на наличие информации о загрузке
    if not upload_success:
        return HttpResponseRedirect(reverse('home'))

    return render(request, 'upload_success.html', {
        'unique_key': upload_success['unique_key'],
        'link': upload_success['link'],
        'file_expiration': upload_success['file_expiration']
    })

def decrypt_file(encrypted_data, key):
    try:
        fernet = Fernet(key.encode())  # Создание объекта Fernet с ключом
        decrypted_data = fernet.decrypt(encrypted_data)  # Дешифрование данных
        return decrypted_data
    except Exception as e:
        logger.error("Ошибка при расшифровке файла: %s", e)  # Логирование ошибок
        return None

def download_file(request, key):
    # Получение записи файла по уникальному ключу
    file_record = get_object_or_404(File, unique_key=key)
    logger.info("Получена запись файла: %s", file_record)

    # Проверка, может ли файл быть скачан (одноразовая ссылка или срок жизни)
    if not file_record.can_be_downloaded():
        logger.warning("Файл недоступен для скачивания. Он был либо уже скачан, либо истек срок его жизни.")
        return HttpResponse("Файл недоступен для скачивания.", status=403)

    with file_record.file.open('rb') as f:
        encrypted_data = f.read()  # Чтение зашифрованных данных
        logger.info("Прочитаны зашифрованные данные, размер: %d байт", len(encrypted_data))

    # Расшифровка данных
    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)
    if decrypted_data is None:
        logger.error("Ошибка: Не удалось расшифровать файл.")
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)
    
    logger.info("Данные расшифрованы.")

    # Определение MIME-типа
    mime_type = file_record.mime_type or mimetypes.guess_type(file_record.file.name)[0]
    if not mime_type:
        mime_type = 'application/octet-stream'
    logger.info("Определённый MIME-тип: %s", mime_type)

    # Получаем расширение файла и имя файла
    original_filename = file_record.file.name
    file_name, file_extension = os.path.splitext(original_filename)
    if not file_extension:
        file_extension = mimetypes.guess_extension(mime_type) or '.bin'
    logger.info("Определённое расширение файла: %s", file_extension)

    filename = f"{file_record.unique_key}{file_extension}"  # Задаем имя файла с расширением
    logger.info("Имя файла для скачивания: %s", filename)

    # Формирование ответа с расшифрованными данными
    response = HttpResponse(decrypted_data, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    logger.info("Файл готов к отправке.")

    # Если файл одноразовый, помечаем его как скачанный и удаляем
    if not file_record.expires_at:  # Если срок жизни не установлен, файл одноразовый
        file_record.mark_as_downloaded()
        delete_file(file_record)
        logger.info("Файл %s был удалён после скачивания (одноразовый файл).", file_record.file.name)
    else:
        logger.info("Файл имеет срок жизни, он не будет удалён после скачивания.")

    return response