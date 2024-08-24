
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from handlers.main_menu import start
from handlers.privacy_policy import accept_policy
from handlers.link_generation import (
    link_lifetime_selected,
    file_type_selected,
    handle_image,
    handle_file,
    handle_video,
)
from handlers.admin_menu import register_handlers as register_admin_handlers  # Импортируйте обработчик админ-меню
from handlers.admin_menu import handle_user_input

# Настройка логирования

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Команда /start
    application.add_handler(CommandHandler("start", start))

    # Обработчики для обычных пользователей
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(CallbackQueryHandler(file_type_selected, pattern='image|file|image_text|video'))
    application.add_handler(CallbackQueryHandler(link_lifetime_selected, pattern='1|1_day|5_days|30_days|90_days'))
    # Обработчики для политики конфиденциальности
    application.add_handler(CallbackQueryHandler(accept_policy, pattern='accept_policy'))

    # Добавьте обработчик админ-меню
    register_admin_handlers(application)  # Подключите обработчик админ-меню    

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
