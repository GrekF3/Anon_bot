# admin_utils.py
from telegram import Update
from telegram.ext import ContextTypes
from db import get_all_users, get_user_profile, block_user as db_block_user

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text  # Получаем текст сообщения для рассылки
    broadcast_image = context.user_data.get('broadcast_image')  # Получаем изображение для рассылки, если оно есть

    users = get_all_users()  # Получаем всех пользователей из базы данных

    for user in users:
        user_id = user[0]  # Получаем user_id из кортежа
        try:
            if broadcast_image:
                # Если изображение есть, отправляем его вместе с текстом
                await context.bot.send_photo(chat_id=user_id, photo=broadcast_image, caption=message_text)
            else:
                # Если изображения нет, отправляем только текст
                await context.bot.send_message(chat_id=user_id, text=message_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    # Уведомляем администратора о завершении рассылки
    await update.message.reply_text("Рассылка завершена.")

    # Очищаем состояние и контекст
    context.user_data['state'] = None
    context.user_data.pop('broadcast_image', None)

async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username_input = update.message.text.strip()
    user_profile = None

    if username_input.isdigit():
        user_id = int(username_input)
        user_profile = get_user_profile(user_id=user_id)
    else:
        user_profile = get_user_profile(username=username_input)

    if user_profile:
        await update.message.reply_text(
            f"Профиль пользователя @{user_profile['username']}:\n"
            f"Тип подписки: {user_profile['subscription_type']}\n"
            f"Сгенерированные ссылки: {user_profile['generated_links']}\n"
            f"Администратор: {'Да' if user_profile['is_admin'] else 'Нет'}\n"
            f"Статус блокировки: {'Да' if user_profile['is_blocked'] else 'Нет'}"
        )
    else:
        await update.message.reply_text("Пользователь не найден.")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.text.strip()
    user_profile = get_user_profile(username=username)

    if user_profile:
        db_block_user(user_profile['user_id'])
        await update.message.reply_text(f"Пользователь @{username} заблокирован.")
    else:
        await update.message.reply_text("Пользователь не найден.")
