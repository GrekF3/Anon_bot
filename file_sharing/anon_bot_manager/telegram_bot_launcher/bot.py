from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import django
from django.conf import settings
from anon_bot_manager.telegram_bot_launcher.handlers.main_menu import start, handle_user_input, show_main_menu, cancel
from anon_bot_manager.telegram_bot_launcher.handlers.link_generation import (
    link_lifetime_selected,
    handle_image,
    handle_file,
    handle_video,
)
from anon_bot_manager.telegram_bot_launcher.handlers.subscription import subscription, handle_payment_selection
from anon_bot_manager.telegram_bot_launcher.handlers.privacy_policy import accept_policy
import os

# Установка Django настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_sharing.settings')
django.setup()

def register_handlers(application: Application) -> None:
    """Регистрирует все обработчики для бота"""
    # Команда /start вызывает start, которое показывает главное меню
    application.add_handler(CommandHandler("start", start))

    # Команда для подписки
    application.add_handler(CommandHandler("subscription", subscription))

    # Обработчик для выбора метода оплаты
    application.add_handler(CallbackQueryHandler(handle_payment_selection, pattern='pay_btc|pay_usdt_trc20|pay_usdt_erc20|pay_eth|pay_xmr'))

    # Основной обработчик текста, проверяет ввод и вызывает соответствующие функции
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Обработчики для загрузки файлов (фото, видео, документы)
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # Обработчик для выбора времени жизни ссылки
    application.add_handler(CallbackQueryHandler(link_lifetime_selected, pattern='1|1_day|5_days|30_days|90_days'))

    # Обработчик для отмены
    application.add_handler(CallbackQueryHandler(cancel, pattern='cancel'))

    # Если нужно было бы добавить политику конфиденциальности:
    application.add_handler(CallbackQueryHandler(accept_policy, pattern='accept_policy'))

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(settings.ANON_TOKEN).build()
    register_handlers(application)
    print('Запускаю бота!')
    # В случае критической ошибки, будет записано сообщение в лог
    try:
        print('Бот был запущен!')
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
