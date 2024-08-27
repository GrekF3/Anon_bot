from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from utils import generate_unique_key
from handlers.privacy_policy import privacy_policy
import requests
from cryptography.fernet import Fernet
from config import API_URL
import asyncio
from db import update_generated_links, get_user_profile
import logging

# Настройка логирования
logging.getLogger("requests").setLevel(logging.WARNING)

# Определение состояний
SELECTING_FILE_TYPE = 'selecting_file_type'
WAITING_FOR_FILE = 'waiting_for_file'
WAITING_FOR_IMAGE_TEXT = 'waiting_for_image_text'

# Генерация уникального ключа шифрования
def generate_encryption_key() -> bytes:
    return Fernet.generate_key()

# Шифрование данных
def encrypt_data(data: bytes, encryption_key: bytes) -> bytes:
    if not data:
        raise ValueError("Data to encrypt cannot be empty.")
    cipher_suite = Fernet(encryption_key)
    return cipher_suite.encrypt(data)

async def generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = SELECTING_FILE_TYPE

    keyboard = [
        [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Пожалуйста, отправьте ваш файл.\n\n"
        "*Обратите внимание, что максимальный размер файла для загрузки в Telegram составляет 20 МБ*.\n\n"
        "Если файл больше, вы можете загрузить его на нашем сайте:",
        reply_markup=reply_markup,
        parse_mode='Markdown'  # Используем Markdown для форматирования
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    
    if state is None:
        await update.message.reply_text("Пожалуйста, сначала отправьте файл.")
        return

    # Обработка входящего файла
    if update.message.document:
        await handle_file(update, context)
    elif update.message.photo:
        await handle_image(update, context)
    elif update.message.video:
        await handle_video(update, context)
    else:
        await update.message.reply_text("Пожалуйста, отправьте файл, изображение или видео.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = await update.message.document.get_file()
    file_size = update.message.document.file_size

    if file_size > 20 * 1024 * 1024:  # 20 MB
        await update.message.reply_text("Файл превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.")
        return

    file_data = await file.download_as_bytearray()
    file_data = bytes(file_data)
    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    context.user_data['uploaded_content'] = {
        'type': 'file',
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()
    }

    await ask_for_link_lifetime(update)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_size = photo.file_size

    if file_size > 20 * 1024 * 1024:  # 20 MB
        await update.message.reply_text("Изображение превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.")
        return

    file_data = await file.download_as_bytearray()
    file_data = bytes(file_data)
    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    context.user_data['uploaded_content'] = {
        'type': 'image',
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()
    }

    await ask_for_link_lifetime(update)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video = update.message.video
    file_size = video.file_size

    if file_size > 20 * 1024 * 1024:  # 20 MB
        await update.message.reply_text("Видео превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.")
        return

    file = await video.get_file()
    file_data = await file.download_as_bytearray()
    file_data = bytes(file_data)

    encryption_key = generate_encryption_key()
    encrypted_data = encrypt_data(file_data, encryption_key)

    context.user_data['uploaded_content'] = {
        'type': 'video',
        'content': encrypted_data,
        'encryption_key': encryption_key.decode()
    }

    await ask_for_link_lifetime(update)

async def ask_for_link_lifetime(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Одноразовая ссылка", callback_data='1')],
        [InlineKeyboardButton("Ссылка на 1 день", callback_data='1_day')],
        [InlineKeyboardButton("Ссылка на 5 дней", callback_data='5_days')],
        [InlineKeyboardButton("Ссылка на 30 дней (подписка)", callback_data='30_days')],
        [InlineKeyboardButton("Ссылка на 90 дней (подписка)", callback_data='90_days')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите срок жизни ссылки:", reply_markup=reply_markup)

async def link_lifetime_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lifetime = query.data
    uploaded_content = context.user_data.get('uploaded_content')

    if not uploaded_content:
        await query.message.reply_text("Ошибка: не найден загруженный контент.")
        return

    unique_key = generate_unique_key()
    files = {'file': uploaded_content['content']}
    data = {
        'key': unique_key,
        'type': uploaded_content['type'],
        'text': context.user_data.get('text', ''),
        'lifetime': lifetime,
        'encryption_key': uploaded_content['encryption_key']
    }

    loading_message = await query.message.edit_text("Загрузка файла на сервер...")

    try:
        response = requests.post(f'{API_URL}/upload/', data=data, files=files)

        if response.status_code == 200:
            response_data = response.json()
            file_url = response_data.get('file_url')
            unique_key = response_data.get('unique_key')

            if file_url is None:
                await loading_message.edit_text("Ошибка: сервер не вернул ссылку на файл.")
                return

            user_id = update.effective_user.id
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
    except requests.RequestException as e:
        await loading_message.edit_text("Ошибка при подключении к серверу. Пожалуйста, попробуйте снова.")
        logging.error(f"Ошибка при запросе: {e}")
