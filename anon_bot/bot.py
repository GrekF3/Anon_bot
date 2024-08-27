from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN
from handlers.main_menu import start
from handlers.privacy_policy import accept_policy
from handlers.link_generation import (
    link_lifetime_selected,
    handle_image,
    handle_file,
    handle_video,
)
from handlers.admin_menu import handle_user_input, cancel
from handlers.subscription import subscription, handle_payment_selection
from db import check_and_init_db

# Настройка логирования (минимальное логирование)
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.CRITICAL  # Уровень логирования только для критических ошибок
)
logger = logging.getLogger(__name__)

def register_handlers(application: Application) -> None:
    """Регистрирует все обработчики для бота"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscription", subscription))
    application.add_handler(CallbackQueryHandler(handle_payment_selection, pattern='pay_btc|pay_usdt_trc20|pay_usdt_erc20|pay_eth|pay_xmr'))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(CallbackQueryHandler(link_lifetime_selected, pattern='1|1_day|5_days|30_days|90_days'))
    application.add_handler(CallbackQueryHandler(cancel, pattern='cancel'))

    application.add_handler(CallbackQueryHandler(accept_policy, pattern='accept_policy'))

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    register_handlers(application)

    # В случае критической ошибки, будет записано сообщение в лог
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")

if __name__ == '__main__':
    check_and_init_db()
    main()
