# main_menu.py

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.privacy_policy import privacy_policy
from db import add_user, get_user_profile


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    context.user_data.clear() 
    add_user(user_id, username)
    user_profile = get_user_profile(user_id)
    if user_profile and not user_profile['user_consent']:  
        await privacy_policy(update, context)
    else:
        await show_main_menu(update)

async def show_main_menu(update: Update) -> None:
    user_id = update.message.from_user.id

    # Получаем информацию о пользователе, включая статус администратора
    user_profile = get_user_profile(user_id)
    is_admin = user_profile['is_admin'] if user_profile else False

    # Основное меню
    keyboard = [
        [KeyboardButton("🔗 Сгенерировать ссылку 🔗")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("Подписка 💰")],
        [KeyboardButton("📕 Политика конфиденциальности 📕")]
    ]

    # Если пользователь администратор, добавляем кнопку для админ-меню
    if is_admin:
        keyboard.append([KeyboardButton("⚙ Администраторское меню ⚙")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)



