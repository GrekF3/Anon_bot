from telegram import Update
from telegram.ext import ContextTypes
from handlers.privacy_policy import privacy_policy
from handlers.link_generation import generate_link
from handlers.profile import profile
from handlers.subscription import subscription
from handlers.main_menu import show_main_menu
from db import get_user_profile
from config import API_URL

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.message.from_user.id
    user_profile = get_user_profile(user_id=user_id)

    if user_profile['is_admin'] == True:
    # Отправляем ссылку на админ-панель вместо меню
        admin_link = f"{API_URL}/bot_admin_page/broadcast/"  # Замените на ваш реальный URL
        await update.message.reply_text(
            f"Вы можете войти в админ-панель по следующей ссылке:\n{admin_link}\n\n"
            "Если у вас есть вопросы, пожалуйста, свяжитесь с поддержкой."
        )
    else:
        pass

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_profile = get_user_profile(user_id=user_id)  # Получаем профиль пользователя

    # Проверка, заблокирован ли пользователь
    if user_profile and user_profile['is_blocked']:
        await update.message.reply_text(
            "Вы были заблокированы на сервисе.\nДля разблокировки свяжитесь с @GrekF3"
        )
        return  # Выходим из функции, чтобы не продолжать обработку

    # Убираем все обработчики для админ-меню
    state = context.user_data.get('state')

    if state == 'admin_menu':
        await show_admin_menu(update, context)
    else:
        # Основное меню
        selected_option = update.message.text
        if selected_option == "🔗 Сгенерировать ссылку 🔗":
            await generate_link(update, context)
        elif selected_option == "👤 Профиль":
            await profile(update, context)
        elif selected_option == "Подписка 💰" or selected_option == "Управление подпиской":
            await subscription(update, context)
        elif selected_option == "📕 Политика конфиденциальности 📕":
            await privacy_policy(update, context)
        elif selected_option == "⚙ Администраторское меню ⚙":
            await show_admin_menu(update,context)
        elif selected_option == "Вернуться в меню":
            await show_main_menu(update)
        else:
            await update.message.reply_text("Неизвестная команда. Пожалуйста, выберите из меню.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем, что колбек был получен

    # Сброс состояния пользователя
    context.user_data['state'] = None  
    context.user_data['uploaded_content'] = None  # Убираем загруженное содержимое, если есть
    # Ответ пользователю
    await query.message.edit_text("Отменено.") 