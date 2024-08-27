from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from database.db import initialize_database, add_user, create_ticket, get_operators, assign_ticket_to_operator, close_ticket, get_ticket_by_id, get_working_tickets, get_open_ticket, get_ticket_info

# Инициализируем базу данных
initialize_database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало диалога с пользователем."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    add_user(user_id, username)
    await update.message.reply_text("Добро пожаловать! Вы можете задать вопрос, и мы вам поможем.")


async def notify_operators_of_user_message(context: ContextTypes.DEFAULT_TYPE, ticket_id: int, user_id: int, question: str) -> None:
    """Уведомляет операторов о новом сообщении от пользователя по открытому тикету."""
    operators_ids = get_operators()  # Получаем список ID операторов
    
    if not operators_ids:
        print("Нет доступных операторов для уведомления.")
        return  # Если нет операторов, выходим из функции

    # Уведомляем каждого оператора о новом сообщении
    for operator_id in operators_ids:
        # Создаем кнопку "Завершить диалог"
        keyboard = [
            [InlineKeyboardButton("Завершить диалог", callback_data=f"end_dialog_{ticket_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=operator_id, 
            text=f"#{ticket_id}: {question}",
            reply_markup=reply_markup  # Добавляем разметку с кнопкой
        )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка сообщения от пользователя и создание тикета."""
    user_id = update.effective_user.id
    question = update.message.text

    # Получаем список ID операторов
    operators_ids = get_operators()

    # Проверяем, является ли пользователь оператором
    if user_id in operators_ids:
        await handle_operator_message(update, context, question)
    else:
        # Проверяем, есть ли у пользователя уже открытый тикет
        open_ticket = get_open_ticket(user_id)  # Проверяем статусы 'in_progress' или 'new'

        if open_ticket:
            # Если открытый тикет существует, уведомляем операторов о новом сообщении пользователя
            ticket_id = open_ticket[0]  # Предполагаем, что первый элемент - это ID тикета
            # Отправляем сообщение оператору, что пользователь ответил по уже открытому тикету
            await notify_operators_of_user_message(context, ticket_id, user_id, question)
        else:
            # Создаем новый тикет в базе данных
            ticket_id = create_ticket(user_id, question)

            # Уведомляем операторов о новом тикете
            await notify_operators(context, ticket_id, user_id, question)

            await update.message.reply_text("Ваш вопрос был зарегистрирован. Ожидайте ответа от оператора.")


async def notify_operators(context: ContextTypes.DEFAULT_TYPE, ticket_id: int, user_id: int, question: str) -> None:
    """Уведомление операторов о новом тикете."""
    operators = get_operators()
    if not operators:
        return  # Если операторов нет, просто выходим из функции

    for operator in operators:
        operator_id = operator  # Получаем ID оператора из кортежа
        keyboard = [
            [InlineKeyboardButton("Взять в работу", callback_data=f"take_{ticket_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=operator_id,
            text=f"👤 Новый вопрос от пользователя: {user_id}\n💬 Вопрос: {question}\n📝 Номер тикета: {ticket_id}",
            reply_markup=reply_markup
        )

async def take_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Оператор берет тикет в работу."""
    query = update.callback_query
    ticket_id = int(query.data.split("_")[1])
    operator_id = update.effective_user.id

    assign_ticket_to_operator(ticket_id, operator_id)

    await query.answer("Вы взяли тикет в работу.")
    await context.bot.send_message(chat_id=operator_id, text="Теперь вы можете общаться с пользователем.")

    # Получаем информацию о тикете
    ticket = get_ticket_by_id(ticket_id)
    user_id = ticket[2]  # user_id из тикета
    await context.bot.send_message(chat_id=user_id, text="Оператор взял ваш вопрос в работу. Вы можете ждать ответа.")

async def finish_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Оператор завершает разговор."""
    query = update.callback_query
    ticket_id = int(query.data.split("_")[1])

    close_ticket(ticket_id)

    await query.answer("Диалог завершен.")
    await context.bot.send_message(chat_id=query.from_user.id, text="Диалог завершен. Спасибо за ваше время!")

async def handle_operator_message(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str) -> None:
    """Обработка сообщений от операторов."""
    operator_id = update.effective_user.id
    message_text = update.message.text

    # Получаем все тикеты, назначенные оператору и находящиеся в работе
    assigned_tickets = get_working_tickets()  # Предполагаем, что эта функция получает только рабочие тикеты
    ticket_found = False  # Флаг для отслеживания, найден ли тикет

    for ticket in assigned_tickets:
        if ticket[3] == operator_id:  # Проверяем, назначен ли оператор на тикет
            user_id = ticket[2]  # Получаем user_id из тикета
            

            await context.bot.send_message(
                chat_id=user_id,
                text=f"{message_text}",
            )
            ticket_found = True
            break  # Выходим из цикла после обработки первого тикета

    if not ticket_found:
        await update.message.reply_text("У вас нет назначенных тикетов для ответа.")



async def end_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка завершения диалога оператором."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    # Получаем ID тикета из callback_data
    ticket_id = int(query.data.split("_")[2])  # Извлекаем ID тикета

    # Закрываем тикет в базе данных
    close_ticket(ticket_id)  # Функция для закрытия тикета

    # Получаем информацию о тикете (например, user_id), чтобы уведомить пользователя
    ticket_info = get_ticket_info(ticket_id)  # Предполагаем, что у вас есть эта функция
    user_id = ticket_info[2]  # Получаем user_id из информации о тикете

    # Уведомляем пользователя о завершении диалога
    await context.bot.send_message(
        chat_id=user_id,
        text="Диалог завершен. Спасибо, что пользуетесь нашим сервисом."
    )

    # Изменяем текст сообщения оператора
    await query.edit_message_text(text=f"Ticket {ticket_id} завершен. Спасибо за вашу работу.")





def main() -> None:
    """Запуск бота."""
    application = Application.builder().token('6793726422:AAGaEZ588yVlgKa7OlcNjDwu2RV5t2Z9yQg').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))  # Обработка сообщений пользователей
    application.add_handler(CallbackQueryHandler(take_ticket, pattern=r"^take_"))  # Обработка нажатий на кнопки "Взять в работу"
    application.add_handler(CallbackQueryHandler(end_dialog, pattern=r"^end_dialog_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_operator_message))  # Обработка сообщений операторов

    application.run_polling()

if __name__ == '__main__':
    main()
