import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import django
from django.conf import settings
from anon_bot_manager.telegram_bot_launcher.handlers.main_menu import start, handle_user_input, cancel
from anon_bot_manager.telegram_bot_launcher.handlers.link_generation import (
    link_lifetime_selected,
    handle_image,
    handle_file,
    handle_video,
    handle_audio,
)
from anon_bot_manager.telegram_bot_launcher.handlers.support import support_bot
from anon_bot_manager.telegram_bot_launcher.handlers.privacy_policy import accept_policy
import os

# Установка Django настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_sharing.settings')
django.setup()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger('httpx').setLevel(logging.WARNING)  # Для новых версий
logging.getLogger('telegram').setLevel(logging.WARNING)  # Для старых версий

def register_handlers(application: Application) -> None:
    """Регистрирует все обработчики для бота"""
    logger.info("Регистрация обработчиков...")
    
    # Команда /start вызывает start, которое показывает главное меню
    application.add_handler(CommandHandler("start", start))
    logger.info("Обработчик /start зарегистрирован")

    # Команда для поддержки
    application.add_handler(CommandHandler("subscription", support_bot))
    logger.info("Обработчик /subscription зарегистрирован")

    # Основной обработчик текста, проверяет ввод и вызывает соответствующие функции
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    logger.info("Обработчик текстовых сообщений зарегистрирован")

    # Обработчики для загрузки файлов (фото, видео, документы)
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    logger.info("Обработчики загрузки файлов зарегистрированы")

    # Обработчик для выбора времени жизни ссылки
    application.add_handler(CallbackQueryHandler(link_lifetime_selected, pattern='one_time|1_day|3_days|7_days'))
    logger.info("Обработчик выбора времени жизни ссылки зарегистрирован")

    # Обработчик для отмены
    application.add_handler(CallbackQueryHandler(cancel, pattern='cancel'))
    logger.info("Обработчик отмены зарегистрирован")

    # Обработчик политики конфиденциальности:
    application.add_handler(CallbackQueryHandler(accept_policy, pattern='accept_policy'))
    logger.info("Обработчик политики конфиденциальности зарегистрирован")

def main() -> None:
    """Запуск бота"""
    logger.info("Инициализация бота...")

    try:
        application = Application.builder().token(settings.ANON_TOKEN).build()
        register_handlers(application)
        logger.info('Бот успешно запущен!')
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.exception("Критическая ошибка при запуске бота: %s", e)

if __name__ == "__main__":
    main()
