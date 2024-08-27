from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_user_profile

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    try:
        user_profile = get_user_profile(user_id=user_id)

        if user_profile:
            # Устанавливаем статус подписки и блокировки
            subscription_status = "✅ Активна" if user_profile['subscription_type'] != 'FREE' else "❌ Неактивна"
            blocked_status = "🚫 Заблокирован" if user_profile['is_blocked'] else "✅ Активен"

            # Формируем текст ответа с использованием Markdown для форматирования
            response_text = (
                "*Профиль пользователя:*\n\n"
                f"👤 *Никнейм:* @{user_profile['username']}\n"
                f"🪙 *Подписка:* {subscription_status}\n"
                f"🔒 *Доступ к сервису:* {blocked_status}\n"
                f"📊 *Сгенерировано ссылок:* {user_profile['generated_links']}\n"
            )

            # Добавляем информацию о роли, если пользователь - администратор
            if user_profile['is_admin']:
                response_text += "👑 *Роль:* Администратор\n"

            # Создаем кнопки для управления подпиской и возвращения в меню
            keyboard = [
                [KeyboardButton("Управление подпиской")],
                [KeyboardButton("Вернуться в меню")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("Профиль не найден.")
    except Exception:
        await update.message.reply_text("Произошла ошибка при получении профиля. Пожалуйста, попробуйте снова позже.")
