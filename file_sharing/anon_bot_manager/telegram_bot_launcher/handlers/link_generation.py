import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from anon_bot_manager.telegram_bot_launcher.utils import generate_unique_key
import requests
from anon_bot_manager.models import BotUser
from django.conf import settings
import mimetypes
import os
from asgiref.sync import sync_to_async

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Определение состояний
SELECTING_FILE_TYPE = 'selecting_file_type'
WAITING_FOR_FILE = 'waiting_for_file'
WAITING_FOR_IMAGE_TEXT = 'waiting_for_image_text'

async def generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Пользователь запрашивает генерацию ссылки")
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
        parse_mode='Markdown'
    )

async def update_generated_links(user_id):
    logger.info(f"Обновление количества сгенерированных ссылок для пользователя с ID {user_id}")
    user = await sync_to_async(BotUser.objects.get)(user_id=user_id)
    user.generated_links += 1
    await sync_to_async(user.save)()
    return

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audio = update.message.audio
    file = await audio.get_file()
    file_size = audio.file_size
    logger.info(f"Обработка аудиофайла размером {file_size} байт")
    keyboard = [
        [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if file_size > 20 * 1024 * 1024:  # 20 MB
        await update.message.reply_text("Файл превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.", reply_markup=reply_markup)
        return

    file_path = file.file_path
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    logger.info(f"MIME-тип аудиофайла: {mime_type}")

    file_data = await file.download_as_bytearray()
    context.user_data['uploaded_content'] = {
        'type': 'audio',
        'content': file_data,
        'mime_type': mime_type,
    }

    await ask_for_link_lifetime(update)

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    file = await document.get_file()
    file_size = document.file_size
    logger.info(f"Обработка файла размером {file_size} байт")
    keyboard = [
        [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if file_size > 20 * 1024 * 1024:  # 20 MB
        logger.warning("Файл превышает допустимый размер в 20 МБ")
        await update.message.reply_text("Файл превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.", reply_markup=reply_markup)
        return

    # Получаем путь к файлу и определяем MIME-тип
    file_path = file.file_path
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    logger.info(f"MIME-тип файла: {mime_type}")

    # Если MIME-тип является изображением, обрабатываем его как изображение
    if mime_type and mime_type.startswith('image/'):
        logger.info('Файл распознан как изображение, передача в обработчик изображений.')
        await handle_image(update, context)
        return

    # Если MIME-тип является аудио, обрабатываем его как аудиофайл
    if mime_type and mime_type.startswith('audio/'):
        logger.info('Файл распознан как аудио, передача в обработчик аудио.')
        await handle_audio(update, context)
        return

    # Обработка как файла в остальных случаях
    file_data = await file.download_as_bytearray()
    context.user_data['uploaded_content'] = {
        'type': 'file',
        'content': file_data,
        'mime_type': mime_type,
    }

    await ask_for_link_lifetime(update)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Если изображение было отправлено как документ, используем этот блок для получения файла
    if update.message.document:
        document = update.message.document
        file = await document.get_file()
        file_size = document.file_size
    else:
        # Если изображение отправлено как фото, используем последний элемент в списке фотографий (самое большое изображение)
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_size = photo.file_size

    keyboard = [
        [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if file_size > 20 * 1024 * 1024:
        logger.warning("Файл превышает допустимый размер в 20 МБ")  # 20 MB
        await update.message.reply_text("Файл превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.", reply_markup=reply_markup)
        return

    file_path = file.file_path
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    logger.info(f"MIME-тип изображения: {mime_type}")

    file_data = await file.download_as_bytearray()
    context.user_data['uploaded_content'] = {
        'type': 'image',
        'content': file_data,
        'mime_type': mime_type,
    }

    await ask_for_link_lifetime(update)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video = update.message.video
    file_size = video.file_size

    keyboard = [
        [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if file_size > 20 * 1024 * 1024:  # 20 MB
        logger.warning("Файл превышает допустимый размер в 20 МБ")
        await update.message.reply_text("Файл превышает ограничение Telegram в 20 МБ. Вы можете загрузить его на нашем сайте.", reply_markup=reply_markup)
        return

    file = await video.get_file()
    file_path = file.file_path
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    logger.info(f"MIME-тип видеофайла: {mime_type}")

    file_data = await file.download_as_bytearray()
    context.user_data['uploaded_content'] = {
        'type': 'video',
        'content': file_data,
        'mime_type' : mime_type,
    }
    await ask_for_link_lifetime(update)


async def ask_for_link_lifetime(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Одноразовая ссылка", callback_data='one_time')],
        [InlineKeyboardButton("Ссылка на 1 день", callback_data='1_day')],
        [InlineKeyboardButton("Ссылка на 3 дня", callback_data='3_days')],
        [InlineKeyboardButton("Ссылка на 7 дней", callback_data='7_days')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите срок жизни ссылки:", reply_markup=reply_markup)
    
async def link_lifetime_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    LIFETIME_DISPLAY = {
        'one_time': 'Одноразовая ссылка',
        '1_day': '1 день',
        '3_days': '3 дня',
        '7_days': '7 дней'
    }
    query = update.callback_query
    await query.answer()

    lifetime = query.data
    lifetime_display = LIFETIME_DISPLAY.get(lifetime, 'Неизвестный срок жизни')
    uploaded_content = context.user_data.get('uploaded_content')

    if not uploaded_content:
        logger.error(f"Ошибка: контент не найден для пользователя {update.effective_user.id}")
        await query.message.reply_text("Ошибка: не найден загруженный контент.")
        return

    unique_key = generate_unique_key()
    logger.info(f"Генерация ссылки с уникальным ключом: {unique_key} для пользователя {update.effective_user.id}")

    # Получаем имя файла и MIME-тип
    original_filename = uploaded_content.get('filename', 'uploaded_file')
    mime_type = uploaded_content['mime_type']
    logger.info(f"Файл для загрузки: {original_filename}, MIME-тип: {mime_type}, срок жизни ссылки: {lifetime_display}")

    files = {
        'file': (original_filename, uploaded_content['content'])  # Используем оригинальное имя и MIME-тип
    }
    data = {
        'key': unique_key,
        'type': uploaded_content['type'],
        'text': context.user_data.get('text', ''),
        'expiry_duration': lifetime,
        'mime_type': mime_type,
    }
    
    loading_message = await query.message.edit_text("Загрузка файла на сервер...")

    try:
        response = requests.post(f'{settings.API_URL}/upload/', data=data, files=files)

        if response.status_code == 200:
            response_data = response.json()
            file_url = response_data.get('file_url')
            unique_key = response_data.get('unique_key')

            if file_url is None:
                logger.error("Ошибка: сервер не вернул ссылку на файл.")
                await loading_message.edit_text("Ошибка: сервер не вернул ссылку на файл.")
                return
            
            logger.info(f"Файл успешно загружен: {file_url} для пользователя {update.effective_user.id}")
            
            if lifetime != 'one_time':
                download_count = 'Неограничено'
            else:
                download_count = '1'

            user_id = update.effective_user.id
            keyboard = [
                [InlineKeyboardButton("anonloader.io", url="https://anonloader.io")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await loading_message.edit_text(
                f"Ваш файл был успешно загружен на сервер.\n"
                f"Ссылка на ваш файл: {settings.BASE_URL}/file/{unique_key}\n"
                f"Ключ доступа к файлу: <code>{unique_key}</code>\n"
                f"Срок жизни файла: {lifetime_display}\n"
                f"Количество доступных открытий ссылки: {download_count}",
                parse_mode='html',
                reply_markup=reply_markup
            )
            await update_generated_links(user_id=user_id)
            context.user_data['state'] = None
        else:
            logger.error(f"Ошибка при загрузке файла, код ответа: {response.status_code}")
            await loading_message.edit_text("Произошла ошибка при загрузке файла.")
    except requests.RequestException as e:
        logger.exception(f"Ошибка подключения к серверу: {e}")
        await loading_message.edit_text("Ошибка при подключении к серверу. Пожалуйста, попробуйте снова.")