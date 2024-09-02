from django.shortcuts import render, redirect
from .models import File
from .forms import UniqueKeyForm, UploadFileForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from cryptography.fernet import Fernet
from django.urls import reverse
import base64
from django.core.files.base import ContentFile
import os


@csrf_exempt
def upload_file(request):
    print("upload_file called")
    error_message = None
    success_message = None

    if request.method == 'POST':
        print("Received POST request")
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        
        try:
            unique_key = request.POST['key']
            file = request.FILES.get('file')
            lifetime = request.POST['lifetime']
            encryption_key = request.POST['encryption_key']
            file_type = request.POST.get('type', 'file')
            text = request.POST.get('text', '')
            chat_id = request.POST.get('chat_id')

            if not file:
                print("No file found in request")
                error_message = 'Файл не был загружен.'
                return render(request, 'upload_file.html', {
                    'error_message': error_message
                })

            print("Creating File object")
            new_file = File.objects.create(
                unique_key=unique_key,
                file=file,
                encryption_key=encryption_key,
                type=file_type,
                text=text if file_type == 'image_text' else None,
                chat_id=chat_id
            )

            print("File object created:", new_file)
            file_url = request.build_absolute_uri(reverse('download_file', args=[unique_key]))
            print("File URL generated:", file_url)

            success_message = 'Файл успешно загружен!'
            return render(request, 'upload_file.html', {
                'success_message': success_message,
                'file_url': file_url
            })

        except KeyError as e:
            print("KeyError occurred:", e)
            error_message = f'Отсутствует поле: {str(e)}'
            return render(request, 'upload_file.html', {
                'error_message': error_message
            })

    # Если не POST запрос, просто отобразим пустую форму
    return render(request, 'upload_file.html', {})


def delete_file(file_record):
    print("delete_file called for file:", file_record)
    file_path = file_record.file.path
    file_record.delete()
    if os.path.exists(file_path):
        print("Deleting file from filesystem:", file_path)
        os.remove(file_path)


def decrypt_file(encrypted_data, key):
    print("decrypt_file called")
    try:
        fernet = Fernet(key.encode())
        decrypted_data = fernet.decrypt(encrypted_data)
        print("File decrypted successfully")
        return decrypted_data
    except Exception as e:
        print("Error during file decryption:", e)
        return None


def download_file(request, key):
    print("download_file called with key:", key)
    try:
        file_record = File.objects.get(unique_key=key)
        print("File record found:", file_record)
    except File.DoesNotExist:
        print("File with key does not exist")
        return HttpResponse("Такого файла не найдено", status=404)

    with file_record.file.open('rb') as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)

    if decrypted_data is None:
        print("Decryption failed")
        return HttpResponse("Не удалось расшифровать файл. Проверьте ключ шифрования.", status=400)

    print("Decryption successful, processing file type:", file_record.type)
    if file_record.type in ['image', 'image_text']:
        image_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'image_data': image_base64,
            'is_image': True,
        })
    elif file_record.type == 'video':
        video_base64 = base64.b64encode(decrypted_data).decode('utf-8')
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'video_data': video_base64,
            'is_video': True,
        })
    else:
        file_content = ContentFile(decrypted_data)
        delete_file(file_record)
        return render(request, 'file_detail.html', {
            'file': file_record,
            'file_content': file_content,
            'is_image': False,
        })


def file_view(request):
    print("file_view called")
    error_message = None
    error_file_message = None
    image_data = None
    video_data = None
    file_url = None
    upload_file = None  # Инициализация переменной

    if request.method == 'POST':
        print("Received POST request")
        form = UniqueKeyForm(request.POST)
        file_form = UploadFileForm(request.POST, request.FILES)

        # Проверяем, какая форма отправлена
        if 'file' in request.FILES:
            print('Поймал файл!')
            if file_form.is_valid():
                # Получаем загруженный файл
                uploaded_file = request.FILES['file']
                print(f"File successfully 'uploaded': {uploaded_file}")
                # Возвращаем сообщение об успешной загрузке
                error_file_message = f"Файл '{uploaded_file.name}' был успешно загружен."
            else:
                # Выводим ошибки валидации формы
                print('Ошибки валидации формы:', file_form.errors)
                error_file_message = "Произошла ошибка при загрузке файла."

        if form.is_valid():
            unique_key = form.cleaned_data['unique_key']
            print("Form is valid, unique_key:", unique_key)
            try:
                file_record = File.objects.get(unique_key=unique_key)
                print("File record found:", file_record)

                with file_record.file.open('rb') as f:
                    encrypted_data = f.read()

                decrypted_data = decrypt_file(encrypted_data, file_record.encryption_key)

                if decrypted_data is None:
                    print("Decryption failed")
                    error_message = "Не удалось расшифровать файл. Проверьте ключ шифрования."
                else:
                    print("Decryption successful, processing file type:", file_record.type)
                    if file_record.type in ['image', 'image_text']:
                        image_data = base64.b64encode(decrypted_data).decode('utf-8')
                    elif file_record.type == 'video':
                        video_data = base64.b64encode(decrypted_data).decode('utf-8')
                    else:
                        file_url = file_record.file.url

                    file_path = file_record.file.path
                    file_record.delete()
                    
                    if os.path.exists(file_path):
                        print("Deleting file from filesystem:", file_path)
                        os.remove(file_path)

                    return render(request, 'file_detail.html', {
                        'file': file_record,
                        'image_data': image_data,
                        'video_data': video_data,
                        'file_url': file_url,
                    })

            except File.DoesNotExist:
                print("File with key does not exist")
                error_message = "Такого файла не существует."
            except Exception as e:
                print("Exception occurred:", e)
                error_message = "Произошла ошибка."

    else:
        form = UniqueKeyForm()
        upload_file = UploadFileForm()  # Инициализация формы файла

    return render(request, 'file_view.html', {
        'form': form,
        'file_form': upload_file,
        'error_message': error_message,
        'error_file_message': error_file_message,
    })