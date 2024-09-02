# views.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from anon_bot_manager.models import BotUser
from asgiref.sync import sync_to_async

async def privacy_policy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    # Получаем информацию о пользователе
    try:
        user_profile = await sync_to_async(BotUser.objects.get)(user_id=user_id)
    except BotUser.DoesNotExist:
        await update.message.reply_text("Пользователь не найден.")
        return
    
    # Проверяем, согласился ли пользователь с политикой
    if user_profile.user_consent:
        await update.message.reply_text(
            "📕 Политика конфиденциальности 📕:\n\n"
            "1. Как работает наш бот и почему он анонимный:\n"
            "Наш бот позволяет вам анонимно обмениваться файлами через Telegram. Мы используем минимальные данные, необходимые для обеспечения работы сервиса. Эти данные включают:\n"
            "- Ваш уникальный идентификатор пользователя в Telegram;\n"
            "- Ваш никнейм в Telegram (если доступен);\n"
            "- Количество сгенерированных ссылок;\n"
            "- Дата присоединения к боту.\n\n"
            "При загрузке файлов мы шифруем их перед отправкой на наш сервер, используя уникальный ключ шифрования. Это гарантирует, что только вы и те, с кем вы поделились ключом, смогут получить доступ к вашему файлу. Мы не сохраняем содержимое файлов в незашифрованном виде, что обеспечивает вашу полную анонимность.\n\n"
            "2. Ответственность пользователя:\n"
            "Пользователь несет полную ответственность за все действия, выполненные через бота, и должен следовать законам своей страны. Мы настоятельно рекомендуем не использовать бот для распространения незаконного контента.\n\n"
            "3. Ограничение ответственности:\n"
            "Создатель бота не несет ответственности за возможное использование бота третьими лицами в противоправных целях.\n\n"
            "4. Обновление политики:\n"
            "Политика конфиденциальности может быть обновлена, чтобы отразить любые изменения. Мы рекомендуем время от времени проверять её на наличие обновлений.",
        )
        return

    keyboard = [[InlineKeyboardButton("Согласен", callback_data='accept_policy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📕 Политика конфиденциальности 📕:\n\n"
        "1. Как работает наш бот и почему он анонимный:\n"
        "Наш бот позволяет вам анонимно обмениваться файлами через Telegram. Мы используем минимальные данные, необходимые для обеспечения работы сервиса. Эти данные включают:\n"
        "- Ваш уникальный идентификатор пользователя в Telegram;\n"
        "- Ваш никнейм в Telegram (если доступен);\n"
        "- Количество сгенерированных ссылок;\n"
        "- Дата присоединения к боту.\n\n"
        "При загрузке файлов мы шифруем их перед отправкой на наш сервер, используя уникальный ключ шифрования. Это гарантирует, что только вы и те, с кем вы поделились ключом, смогут получить доступ к вашему файлу. Мы не сохраняем содержимое файлов в незашифрованном виде, что обеспечивает вашу полную анонимность.\n\n"
        "2. Ответственность пользователя:\n"
        "Пользователь несет полную ответственность за все действия, выполненные через бота, и должен следовать законам своей страны. Мы настоятельно рекомендуем не использовать бот для распространения незаконного контента.\n\n"
        "3. Ограничение ответственности:\n"
        "Создатель бота не несет ответственности за возможное использование бота третьими лицами в противоправных целях.\n\n"
        "4. Обновление политики:\n"
        "Политика конфиденциальности может быть обновлена, чтобы отразить любые изменения. Мы рекомендуем время от времени проверять её на наличие обновлений.",
        reply_markup=reply_markup
    )

async def accept_policy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    # Отметим, что пользователь согласился с политикой конфиденциальности в базе данных
    try:
        user_profile = await sync_to_async(BotUser.objects.get)(user_id=user_id)
        user_profile.user_consent = True
        await sync_to_async(user_profile.save)()
    except BotUser.DoesNotExist:
        await query.message.reply_text("Пользователь не найден.")
        return

    # Обновляем текст политики конфиденциальности и заменяем кнопку на "Согласен ✅"
    keyboard = [[InlineKeyboardButton("Согласен ✅", callback_data='accepted_policy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Спасибо, что согласились с политикой конфиденциальности! Теперь вы можете использовать генерацию ссылок.",
        reply_markup=reply_markup
    )

    # Показываем главное меню
    keyboard = [
        [KeyboardButton("🔗 Сгенерировать ссылку 🔗")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("Подписка 💰")],
        [KeyboardButton("📕 Политика конфиденциальности 📕")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await query.message.reply_text("Добро пожаловать! Выберите опцию для продолжения:", reply_markup=reply_markup)