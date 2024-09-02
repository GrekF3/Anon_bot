from django.shortcuts import render, redirect
from .models import File
from .forms import UniqueKeyForm
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
                return JsonResponse({'error': 'Файл не был загружен.'}, status=400)

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

            return JsonResponse({
                'message': 'File uploaded successfully!',
                'file_id': new_file.id,
                'file_url': file_url,
                'unique_key': unique_key
            })

        except KeyError as e:
            print("KeyError occurred:", e)
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)

    print("Invalid request method")
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


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
    image_data = None
    video_data = None
    file_url = None

    if request.method == 'POST':
        print("Received POST request")
        form = UniqueKeyForm(request.POST)
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

            except Exception as e:
                print("Exception occurred:", e)
                error_message = "Такого файла не существует."

    else:
        form = UniqueKeyForm()

    return render(request, 'file_view.html', {
        'form': form,
        'error_message': error_message,
    })


