from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import generate_unique_key
from handlers.privacy_policy import privacy_policy
import requests
from cryptography.fernet import Fernet
from config import API_URL
import asyncio  # Импортируем asyncio
from db import update_generated_links

# Определение состояний
SELECTING_FILE_TYPE = 'selecting_file_type'
WAITING_FOR_IMAGE = 'waiting_for_image'
WAITING_FOR_FILE = 'waiting_for_file'
WAITING_FOR_VIDEO = 'waiting_for_video'
WAITING_FOR_IMAGE_TEXT = 'waiting_for_image_text'

# Генерация уникального ключа шифрования
def generate_encryption_key() -> bytes:
    return Fernet.generate_key()

# Шифрование данных
def encrypt_data(data: bytes, encryption_key: bytes) -> bytes:
    cipher_suite = Fernet(encryption_key)
    return cipher_suite.encrypt(data)

async def generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Устанавливаем состояние выбора типа файла
    context.user_data['state'] = SELECTING_FILE_TYPE
    
    # Шаг 1: Выбор типа файла
    keyboard = [
        [InlineKeyboardButton("Изображение", callback_data='image')],
        [InlineKeyboardButton("Файл", callback_data='file')],
        [InlineKeyboardButton("Видео", callback_data='video')],
        [InlineKeyboardButton("Изображение + Текст", callback_data='image_text')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите тип файла:", reply_markup=reply_markup)

async def file_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    file_type = query.data
    context.user_data['selected_file_type'] = file_type

    if file_type == 'image':
        context.user_data['state'] = WAITING_FOR_IMAGE
        await query.message.edit_text("Пожалуйста, отправьте изображение.")
    elif file_type == 'file':
        context.user_data['state'] = WAITING_FOR_FILE
        await query.message.edit_text("Пожалуйста, отправьте файл.")
    elif file_type == 'video':
        context.user_data['state'] = WAITING_FOR_VIDEO  # Устанавливаем состояние ожидания видео
        await query.message.edit_text("Пожалуйста, отправьте видео.")
    elif file_type == 'image_text':
        context.user_data['state'] = WAITING_FOR_IMAGE_TEXT
        await query.message.edit_text("Пожалуйста, отправьте изображение. Затем, отправьте текст.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    print(state + ' handle_message')
    # Проверяем, что состояние установлено, если нет — игнорируем сообщение
    if state is None:
        await update.message.reply_text("Пожалуйста, сначала выберите тип файла.")
        return

    if state == WAITING_FOR_IMAGE:
        await handle_image(update, context)
    elif state == WAITING_FOR_FILE:
        await handle_file(update, context)
    elif state == WAITING_FOR_VIDEO:  # Если ожидается видео
        await handle_video(update, context)
    elif state == WAITING_FOR_IMAGE_TEXT:
        if 'text' not in context.user_data:  # Ожидаем изображение
            await handle_image_with_text(update, context)
        else:  # Ожидаем текст
            context.user_data['text'] = update.message.text  # Сохраняем текст
            await ask_for_link_lifetime(update)
            
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    photo = update.message.photo[-1]  # Получаем самое большое изображение
    file = await photo.get_file()  # Получаем объект файла

    if state == 'broadcast_message':
        # Сохраняем изображение для последующей рассылки
        context.user_data['broadcast_image'] = file.file_id
        await update.message.reply_text("Изображение для рассылки сохранено. Теперь можете отправить текст.")

    elif state == WAITING_FOR_IMAGE:
        # Обработка изображения для генерации ссылки
        file_data = await file.download_as_bytearray()  # Загружаем файл как байтовый массив

        # Преобразуем bytearray в bytes
        file_data = bytes(file_data)

        # Генерация ключа шифрования и шифрование данных
        encryption_key = generate_encryption_key()
        encrypted_data = encrypt_data(file_data, encryption_key)

        # Сохраняем зашифрованный файл и ключ в контексте
        context.user_data['uploaded_content'] = {
            'type': 'image',
            'content': encrypted_data,
            'encryption_key': encryption_key.decode()  # Сохраняем ключ как строку
        }

        await ask_for_link_lifetime(update)  # Спрашиваем о сроке жизни ссылки

    elif state == WAITING_FOR_IMAGE_TEXT:
        # Обработка изображения с последующим ожиданием текста
        file_data = await file.download_as_bytearray()
        if isinstance(file_data, bytearray):
            file_data = bytes(file_data)  # Преобразование в bytes
        elif not isinstance(file_data, bytes):
            await update.message.reply_text("Ошибка: данные не являются байтовым массивом.")
            return

        encryption_key = generate_encryption_key()
        encrypted_data = encrypt_data(file_data, encryption_key)

        context.user_data['uploaded_content'] = {
            'type': 'image_text',
            'content': encrypted_data,
            'encryption_key': encryption_key.decode()
        }

        await update.message.reply_text("Теперь добавьте текст к изображению.")
        print(state + ' Это стейт после захвата изображения')

    else:
        # Если состояние не поддерживается
        await update.message.reply_text("Пожалуйста, сначала выберите действие.")



async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video = update.message.video  # Получаем видео
    file = await video.get_file()  # Ожидаем получения файла
    file_data = await file.download_as_bytearray()  # Загружаем файл как байтовый массив

    # Преобразуем bytearray в bytes
    if isinstance(file_data, bytearray):
        file_data = bytes(file_data)  # Преобразование в bytes
    elif not isinstance(file_data, bytes):
        await update.message.reply_text("Ошибка: данные не являются байтовым массивом.")
        return

    # Генерация ключа шифрования и шифрование данных
    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    # Сохранение зашифрованного файла и ключа шифрования в контексте
    context.user_data['uploaded_content'] = {
        'type': 'video',  # Указываем тип контента
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()  # Сохраняем ключ как строку
    }

    await ask_for_link_lifetime(update)



async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = await update.message.document.get_file()
    file_data = await file.download_as_bytearray()  # Загружаем файл как байтовый массив

    # Преобразуем bytearray в bytes
    if isinstance(file_data, bytearray):
        file_data = bytes(file_data)  # Преобразование в bytes
    elif not isinstance(file_data, bytes):
        await update.message.reply_text("Ошибка: данные не являются байтовым массивом.")
        return

    # Генерация ключа шифрования и шифрование данных
    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    # Сохранение зашифрованного файла и ключа шифрования в контексте
    context.user_data['uploaded_content'] = {
        'type': 'file',
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()  # Сохраняем ключ как строку
    }
    
    await ask_for_link_lifetime(update)


async def handle_image_with_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    
    # Если состояние не соответствует ожиданиям, игнорируем изображение
    if state != WAITING_FOR_IMAGE_TEXT:
        await update.message.reply_text("Пожалуйста, сначала выберите тип файла.")
        return

    photo = update.message.photo[-1]  # Получаем самое большое изображение
    file_data = await photo.get_file().download_as_bytearray()  # Загрузим файл как байтовый массив

    # Генерация ключа шифрования и шифрование данных
    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    # Сохранение зашифрованного файла и ключа шифрования в контексте
    context.user_data['uploaded_content'] = {
        'type': 'image_text',
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()  # Сохраняем ключ как строку
    }

    await update.message.reply_text("Теперь добавьте текст к изображению.")  # Здесь можно ожидать текст

async def ask_for_link_lifetime(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Одноразовая ссылка", callback_data='1')],
        [InlineKeyboardButton("Ссылка на 1 день", callback_data='1_day')],
        [InlineKeyboardButton("Ссылка на 5 дней", callback_data='5_days')],
        [InlineKeyboardButton("Ссылка на 30 дней (подписка)", callback_data='30_days')],
        [InlineKeyboardButton("Ссылка на 90 дней (подписка)", callback_data='90_days')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите срок жизни ссылки:", reply_markup=reply_markup)

async def link_lifetime_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    query = update.callback_query
    await query.answer()

    # Получаем выбранный срок жизни ссылки
    lifetime = query.data
    uploaded_content = context.user_data.get('uploaded_content')

    if not uploaded_content:
        await query.message.reply_text("Ошибка: не найден загруженный контент.")
        return

    # Генерация уникального ключа
    unique_key = generate_unique_key()
    
    # Подготовка данных для отправки на сервер
    files = {'file': uploaded_content['content']}
    data = {
        'key': unique_key,
        'type': uploaded_content['type'],
        'text': context.user_data.get('text', ''),
        'lifetime': lifetime,
        'encryption_key': uploaded_content['encryption_key']  # Передаем ключ шифрования на сервер
    }

    # Отправляем сообщение о начале загрузки
    loading_message = await query.message.edit_text("Загрузка файла на сервер...")

    # Задержка перед отправкой файла на сервер
    await asyncio.sleep(1)  # Ожидание 1 секунду

    # Отправка файла на сервер Django
    response = requests.post(f'{API_URL}/upload/', data=data, files=files)

    if response.status_code == 200:
        response_data = response.json()
        file_url = response_data.get('file_url')
        unique_key = response_data.get('unique_key')

        if file_url is None:
            await loading_message.edit_text("Ошибка: сервер не вернул ссылку на файл.")
            return
        user_id = update.effective_user.id
        # Успешная загрузка
        await loading_message.edit_text(
            f"Ваш файл был успешно загружен на сервер.\n"
            f"Ссылка на ваш файл: {file_url}\n"
            f"Ключ доступа к файлу: <code>{unique_key}</code>\n"
            f"Срок жизни файла: {lifetime}\n"
            f"Количество доступных открытий файла: 1",
            parse_mode='html'
        )
        update_generated_links(user_id=user_id)
        context.user_data['state'] = None
    else:
        await loading_message.edit_text("Произошла ошибка при загрузке файла.")