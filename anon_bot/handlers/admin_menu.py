# admin_menu.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from db import get_statistics
from handlers.privacy_policy import privacy_policy
from handlers.link_generation import generate_link
from handlers.profile import profile
from handlers.subscription import subscription
from handlers.admin_utils import handle_broadcast_message, search_user, block_user  # Импорт функций
from handlers.link_generation import ask_for_link_lifetime

# Этапы разговора
ADMIN_MENU = 'admin_menu'
BROADCAST_MESSAGE = 'broadcast_message'
SEARCH_USER = 'search_user'
BLOCK_USER = 'block_user'

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = 'admin_menu'  # Устанавливаем состояние админа

    keyboard = [
        [InlineKeyboardButton("📢 Сделать рассылку", callback_data='broadcast')],
        [InlineKeyboardButton("👤 Управление пользователями", callback_data='manage_users')],
        [InlineKeyboardButton("📊 Статистика", callback_data='statistics')],
        [InlineKeyboardButton("🔍 Поиск пользователя", callback_data='search_user')],
        [InlineKeyboardButton("💼 Управление подписками", callback_data='manage_subscriptions')],
        [InlineKeyboardButton("🚫 Блокировка пользователей", callback_data='block_user')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите админскую опцию:', reply_markup=reply_markup)

async def handle_admin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'broadcast':
        await query.message.reply_text("Введите сообщение для рассылки:")
        context.user_data['state'] = BROADCAST_MESSAGE
    elif query.data == 'search_user':
        await query.message.reply_text("Введите имя пользователя (username):")
        context.user_data['state'] = SEARCH_USER
    elif query.data == 'block_user':
        await query.message.reply_text("Введите имя пользователя (username) для блокировки:")
        context.user_data['state'] = BLOCK_USER
    elif query.data == 'manage_users':
        await query.message.reply_text("Функция управления пользователями в разработке.")
    elif query.data == 'statistics':
        statistics = get_statistics()  # Получение статистики из базы данных
        await query.message.reply_text(
            f"Количество пользователей: {statistics['user_count']}\n"
            f"Количество сгенерированных ссылок: {statistics['link_count']}\n"
            f"Активные подписки: {statistics['active_subscriptions']}"
        )
    elif query.data == 'manage_subscriptions':
        await query.message.reply_text("Функция управления подписками в разработке.")
    else:
        await query.message.reply_text("Неизвестная команда. Пожалуйста, выберите из меню.")

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    
    if state == BROADCAST_MESSAGE:
        await handle_broadcast_message(update, context)
        context.user_data['state'] = None
    elif state == SEARCH_USER:
        await search_user(update, context)
        context.user_data['state'] = None
    elif state == BLOCK_USER:
        await block_user(update, context)
        context.user_data['state'] = None
    elif state == 'admin_menu':
        await handle_admin_selection(update, context)
    elif state == 'waiting_for_image_text':
        context.user_data['text'] = update.message.text
        await ask_for_link_lifetime(update)
    else:
        # Основное меню
        selected_option = update.message.text
        if selected_option == "🔗 Сгенерировать ссылку 🔗":
            await generate_link(update, context)
        elif selected_option == "👤 Профиль":
            await profile(update, context)
        elif selected_option == "💼 Реферальная система 💼":
            await update.message.reply_text("Это реферальная система.")
        elif selected_option == "Подписка 💰":
            await subscription(update, context)
        elif selected_option == "📕 Политика конфиденциальности 📕":
            await privacy_policy(update, context)
        elif selected_option == "⚙ Администраторское меню ⚙":
            await show_admin_menu(update, context)
        else:
            await update.message.reply_text("Неизвестная команда. Пожалуйста, выберите из меню.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Диалог отменён.")
    context.user_data['state'] = None  # Сброс состояния

def register_handlers(dp):
    dp.add_handler(CallbackQueryHandler(handle_admin_selection, pattern='broadcast|manage_users|statistics|search_user|manage_subscriptions|block_user'))
    dp.add_handler(CommandHandler('cancel', cancel))
