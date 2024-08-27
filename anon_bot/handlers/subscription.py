from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Команда для отображения информации о подписке
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Текст с информацией о преимуществах подписки
    subscription_text = (
        "Подписка на наш сервис дает следующие преимущества:\n\n"
        "1. Увеличенный срок жизни ссылок.\n"
        "2. Лимит на создание ссылок: 100 ссылок в день.\n"
        "3. Загрузка файлов без очереди.\n\n"
        "Выберите способ оплаты ниже:"
    )
    
    # Кнопки для выбора криптовалюты
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить BTC", callback_data='pay_btc')],
        [InlineKeyboardButton("💳 Оплатить USDT (TRC20)", callback_data='pay_usdt_trc20')],
        [InlineKeyboardButton("💳 Оплатить USDT (ERC20)", callback_data='pay_usdt_erc20')],
        [InlineKeyboardButton("💳 Оплатить ETH", callback_data='pay_eth')],
        [InlineKeyboardButton("💳 Оплатить Monero", callback_data='pay_xmr')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправка сообщения пользователю
    await update.message.reply_text(subscription_text, reply_markup=reply_markup)

# Обработчик нажатия на кнопки оплаты
async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Получение выбранной криптовалюты
    selected_payment_method = query.data

    # В зависимости от выбранного метода оплаты отправляем разные инструкции
    if selected_payment_method == 'pay_btc':
        await query.message.reply_text("Для оплаты через BTC используйте следующий адрес: <BTC_ADDRESS>")
    elif selected_payment_method == 'pay_usdt_trc20':
        await query.message.reply_text("Для оплаты через USDT (TRC20) используйте следующий адрес: <USDT_TRC20_ADDRESS>")
    elif selected_payment_method == 'pay_usdt_erc20':
        await query.message.reply_text("Для оплаты через USDT (ERC20) используйте следующий адрес: <USDT_ERC20_ADDRESS>")
    elif selected_payment_method == 'pay_eth':
        await query.message.reply_text("Для оплаты через ETH используйте следующий адрес: <ETH_ADDRESS>")
    elif selected_payment_method == 'pay_xmr':
        await query.message.reply_text("Для оплаты через Monero используйте следующий адрес: <XMR_ADDRESS>")
    else:
        await query.message.reply_text("Неизвестный способ оплаты. Пожалуйста, выберите из списка.")