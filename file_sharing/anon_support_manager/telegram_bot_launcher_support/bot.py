import os
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from django.conf import settings
from anon_support_manager.models import User, Ticket, Operator
from django.utils import timezone
from asgiref.sync import sync_to_async

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_sharing.settings')
django.setup()

# Асинхронные функции взаимодействия с базой данных
async def get_or_create_user(user_id, username):
    user, created = await sync_to_async(User.objects.get_or_create)(user_id=user_id, defaults={'username': username})
    if not created:
        user.username = username
        await sync_to_async(user.save)()
    return user

async def get_operator_by_user(user):
    try:
        operator = await sync_to_async(Operator.objects.get)(user=user)
        return operator
    except Operator.DoesNotExist:
        return None

# Основные команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает бот и регистрирует пользователя."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user = await get_or_create_user(user_id, username)

    welcome_message = "Добро пожаловать! Вы можете задать вопрос, и мы вам поможем."
    await update.message.reply_text(welcome_message)

    # Проверяем, является ли пользователь оператором
    operator = await get_operator_by_user(user)
    if operator:
        await operator_menu(update, context)

async def operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню оператора с доступными действиями."""
    keyboard = [
        [KeyboardButton("Начать смену")],
        [KeyboardButton("Проверить тикеты")],
        [KeyboardButton("Закончить смену")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def start_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает смену оператора."""
    user_id = update.effective_user.id
    operator = await get_operator_by_user(await get_or_create_user(user_id, update.effective_user.username))

    if operator:
        operator.is_active = True
        await sync_to_async(operator.save)()
        await operator_menu(update, context)
        await update.message.reply_text("Смена начата. Вы можете получать тикеты.")
    else:
        await update.message.reply_text("Вы не являетесь оператором.")

async def end_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает смену оператора."""
    user_id = update.effective_user.id
    operator = await get_operator_by_user(await get_or_create_user(user_id, update.effective_user.username))

    if operator:
        operator.is_active = False
        await sync_to_async(operator.save)()
        await update.message.reply_text("Смена завершена.")
        await operator_menu(update, context)
    else:
        await update.message.reply_text("Вы не являетесь оператором.")

async def send_available_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет доступные тикеты активным операторам."""
    available_tickets = await sync_to_async(list)(Ticket.objects.filter(status='new', assigned_user__isnull=True))
    active_operators = await sync_to_async(list)(Operator.objects.filter(is_active=True))

    if not active_operators:
        await update.message.reply_text("Нет доступных операторов.")
        return
    if not available_tickets:
        await update.message.reply_text("Нет доступных тикетов.")
        return

    for operator in active_operators:
        user = await sync_to_async(lambda: operator.user)()
        
        if not user:
            continue

        for ticket in available_tickets:
            keyboard = [
                [InlineKeyboardButton("Взять в работу", callback_data=f"take_{ticket.ticket_id}")],
                [InlineKeyboardButton("Закрыть тикет", callback_data=f"close_{ticket.ticket_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=user.user_id,
                    text=f"Доступный тикет: #{ticket.ticket_id}\nВопрос: {ticket.question or 'Нет вопроса'}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Ошибка при отправке сообщения оператору {user.username}: {e}")

            available_tickets.remove(ticket)
            break

    if available_tickets:
        await update.message.reply_text("Некоторые тикеты не были распределены из-за отсутствия доступных операторов.")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения от пользователей и операторов."""
    user_id = update.effective_user.id
    question = update.message.text
    user = await get_or_create_user(user_id, update.effective_user.username)

    operator = await get_operator_by_user(user)
    if operator:
        if question == "Начать смену":
            await start_shift(update, context)
            return
        elif question == "Закончить смену":
            await end_shift(update, context)
            return
        elif question == "Проверить тикеты":
            await send_available_tickets(update, context)
            return
        elif operator.is_active:
            await handle_operator_message(update, context)
            return

    # Check if the user has an open ticket
    open_ticket = await sync_to_async(lambda: Ticket.objects.filter(user=user, status__in=['in_progress', 'new']).first())()

    if open_ticket:
        ticket_id = await sync_to_async(lambda: open_ticket.ticket_id)()
        operator_user = await sync_to_async(lambda: open_ticket.assigned_user)()
        if operator_user:
            keyboard = [[InlineKeyboardButton("Завершить диалог", callback_data=f"end_dialog_{ticket_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=operator_user.user_id, text=f"Пользователь #{ticket_id} спросил: {question}", reply_markup=reply_markup)
        else:
            await notify_operators_of_user_message(context, ticket_id, user_id, question)
    else:
        # If no open ticket exists, notify all active operators
        ticket = await sync_to_async(Ticket.objects.create)(
            user=user,
            question=question,
            status='new',
            created_at=timezone.now()
        )
        await notify_operators(context, ticket.ticket_id, user_id, question)
        await update.message.reply_text("Ваш вопрос был зарегистрирован. Ожидайте ответа от оператора.")

async def handle_operator_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения от операторов."""
    operator_id = update.effective_user.id
    message_text = update.message.text

    assigned_tickets = await sync_to_async(list)(Ticket.objects.filter(assigned_user__user_id=operator_id, status='in_progress'))

    if not assigned_tickets:
        await update.message.reply_text("У вас нет назначенных тикетов для ответа.")
        return

    ticket = assigned_tickets[0]
    ticket_user = await sync_to_async(lambda: ticket.user.user_id)()
    await context.bot.send_message(chat_id=ticket_user, text=f"{message_text}")

async def notify_operators_of_user_message(context: ContextTypes.DEFAULT_TYPE, ticket_id: int, user_id: int, question: str) -> None:
    """Уведомляет операторов о сообщении от пользователя."""
    operators = await sync_to_async(list)(Operator.objects.filter(is_active=True))
    if not operators:
        return
    for operator in operators:
        chat_id = await sync_to_async(lambda: operator.user.user_id)()
        await context.bot.send_message(chat_id=chat_id, text=f"#{ticket_id}: {question}")



async def notify_operators(context: ContextTypes.DEFAULT_TYPE, ticket_id: int, user_id: int, question: str) -> None:
    """Уведомляет операторов о новом тикете."""
    operators = await sync_to_async(list)(Operator.objects.filter(is_active=True))
    if not operators:
        return

    for operator in operators:
        keyboard = [
            [InlineKeyboardButton("Взять в работу", callback_data=f"take_{ticket_id}")],
            [InlineKeyboardButton("Закрыть тикет", callback_data=f"close_{ticket_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=await sync_to_async(lambda: operator.user.user_id)(),
            text=f"👤 Новый вопрос от пользователя: {user_id}\n💬 Вопрос: {question}\n📝 Номер тикета: {ticket_id}",
            reply_markup=reply_markup
        )

async def end_dialog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает завершение диалога по запросу оператора."""
    query = update.callback_query
    await query.answer()

    try:
        ticket_id = int(query.data.split("_")[2])
        ticket = await sync_to_async(Ticket.objects.get)(ticket_id=ticket_id)
        
        if ticket.status != 'closed':
            ticket.status = 'closed'
            
            user_id = await sync_to_async(lambda: ticket.user.user_id)()
            operator_id = await sync_to_async(lambda: ticket.assigned_user.user_id)()

            await context.bot.send_message(chat_id=user_id, text="Ваш диалог был завершен. Спасибо, что пользуетесь нашим сервисом!")
            await context.bot.send_message(chat_id=operator_id, text="Диалог завершен.")
            
            await query.edit_message_text(f"Диалог по тикету #{ticket_id} завершен.")
            await sync_to_async(ticket.save)()
        else:
            await query.edit_message_text(f"Тикет #{ticket_id} уже закрыт.")
    except (ValueError, Ticket.DoesNotExist):
        await query.edit_message_text("Ошибка при завершении диалога. Тикет не найден.")

async def take_ticket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос оператора на взятие тикета в работу."""
    query = update.callback_query
    await query.answer()
    
    try:
        ticket_id = int(query.data.split("_")[1])
        ticket = await sync_to_async(Ticket.objects.get)(ticket_id=ticket_id)
        question = await sync_to_async(lambda: ticket.question)()
        
        operator = await get_operator_by_user(await get_or_create_user(update.effective_user.id, update.effective_user.username))
        work_operator = await sync_to_async(lambda: ticket.assigned_user)()
        if work_operator is None:
            ticket.status = 'in_progress'
            ticket.assigned_user = await sync_to_async(lambda: operator.user)()
            keyboard = [
                [InlineKeyboardButton("Закрыть тикет", callback_data=f"close_{ticket_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await sync_to_async(ticket.save)()
            await query.edit_message_text(f"Вы взяли тикет #{ticket_id} в работу.\n\n Вопрос:{question}", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Этот тикет уже взят в работу или недоступен.")
    except (ValueError, Ticket.DoesNotExist):
        await query.edit_message_text("Ошибка при обработке тикета. Попробуйте еще раз.")

async def close_ticket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос оператора на закрытие тикета."""
    query = update.callback_query
    await query.answer()
    
    try:
        ticket_id = int(query.data.split("_")[1])
        ticket = await sync_to_async(Ticket.objects.get)(ticket_id=ticket_id)
        
        if ticket.status != 'closed':
            ticket.status = 'closed'
            user_id = await sync_to_async(lambda: ticket.user.user_id)()
            await context.bot.send_message(chat_id=user_id, text="Ваш тикет был закрыт оператором. Спасибо за использование нашего сервиса!")
            await query.edit_message_text(f"Тикет #{ticket_id} был закрыт.")
            await sync_to_async(ticket.save)()
        else:
            await query.edit_message_text(f"Тикет #{ticket_id} уже закрыт.")
    except (ValueError, Ticket.DoesNotExist):
        await query.edit_message_text("Ошибка при закрытии тикета. Попробуйте еще раз.")

# Инициализация бота и команд
def main():
    application = Application.builder().token(settings.ANON_SUPPORT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    application.add_handler(CallbackQueryHandler(end_dialog_handler, pattern=r"end_dialog_\d+"))
    application.add_handler(CallbackQueryHandler(take_ticket_handler, pattern=r"take_\d+"))
    application.add_handler(CallbackQueryHandler(close_ticket_handler, pattern=r"close_\d+"))

    application.run_polling()

if __name__ == "__main__":
    main()
