# handlers/subscription.py
from telegram import Update
from telegram.ext import ContextTypes

async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Подписка:\n\nВы можете увеличить количество ссылок, которые можно генерировать в день...")
