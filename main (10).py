from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
import logging

# логи
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = '7016214070:AAEfNHq7Mf05lzd1BraZVsOCUqb_7H6hSKU'
PAGE_SIZE = 5

# данные о вечеринках
event_data = {}

def save_event_to_db(user_id, event_info):
    #работа с базой данных (создание/подключение)
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            theme TEXT,
            dress_code TEXT,
            address TEXT,
            date_time TEXT,
            event_type TEXT,
            invited_users TEXT
        )
    ''')

    invited_users = ','.join(event_info.get('invited_users', []))
    data_tuple = (user_id, event_info.get('name'), event_info.get('theme'), event_info.get('dress_code'),
                  event_info.get('address'), event_info.get('date_time'), event_info.get('type'), invited_users)

    cursor.execute('''
        INSERT INTO events (user_id, name, theme, dress_code, address, date_time, event_type, invited_users)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data_tuple)

    # сохранить и выйти
    conn.commit()
    conn.close()
    logging.info(f"Event saved for user {user_id}: {event_info}")

def fetch_open_events():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE event_type = 'open'")
    events = cursor.fetchall()
    conn.close()
    return events

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query:
        await query.answer()

    if 'page' not in context.user_data:
        context.user_data['page'] = 0

    page = context.user_data['page']
    events = fetch_open_events()
    page_count = len(events) // PAGE_SIZE + (1 if len(events) % PAGE_SIZE > 0 else 0)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    events_page = events[start:end]

    buttons = [[InlineKeyboardButton(event[2], callback_data=f'event_{event[0]}')] for event in events_page]
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data='prev_page'))
    if page < page_count - 1:
        navigation_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data='next_page'))

    buttons.append(navigation_buttons)
    buttons.append([InlineKeyboardButton("Назад в меню", callback_data='back_to_menu')])

    reply_markup = InlineKeyboardMarkup(buttons)
    if query:
        await query.edit_message_text(text="Выберите мероприятие для просмотра деталей:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text="Выберите мероприятие для просмотра деталей:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = query.from_user.id

    logger.info(f"Button data received: {callback_data}")

    # логика кнопок и обработка
    if callback_data == 'help':
        buttons = [
            [InlineKeyboardButton("УСТРОИТЬ ВЕЧЕРИНКУ!", callback_data='add_event')],
            [InlineKeyboardButton("Джессика, какие тусы на примете?", callback_data='show_events')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text="Используй команды:\n"
                                           "- Чтобы организовать вписку, нажми 'Добавить мероприятие'.\n"
                                           "- Ищешь COOL тусовку??? нажми 'Показать мероприятия'.",
                                      reply_markup=reply_markup)
    elif callback_data == 'add_event':
        event_data[user_id] = {'name': '', 'theme': '', 'dress_code': '', 'address': '', 'date_time': '', 'type': '', 'invited_users': []}
        await query.edit_message_text(text="как назовём вписку?:")
        context.user_data['state'] = 'entering_name'
    elif callback_data == 'show_events':
        await show_events(update, context)
    elif callback_data.startswith('event_'):
        event_id = int(callback_data.split('_')[1])
        event = fetch_event_details(event_id)
        if event:
            await query.edit_message_text(text=format_event_details(event))
        else:
            await query.edit_message_text(text="чё? НЕ НАЙДЕНО!")
    elif callback_data == 'next_page' or callback_data == 'prev_page':
        if 'page' not in context.user_data:
            context.user_data['page'] = 0

        context.user_data['page'] += 1 if callback_data == 'next_page' else -1
        await show_events(update, context)
    elif callback_data == 'back_to_menu':
        await start(update, context)

    # тип события/подтверждение
    user_event_data = event_data.get(user_id, {})
    if callback_data in ['open_event', 'private_event']:
        user_event_data['type'] = 'open' if callback_data == 'open_event' else 'private'
        buttons = [
            [InlineKeyboardButton("НАЧИНАЕМ!!!!", callback_data='confirm_event')],
            [InlineKeyboardButton("Я ПЕРЕДУМАЛ(-A)!", callback_data='cancel_event')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            text=f"Вечеринка будет {'открытой' if user_event_data['type'] == 'open' else 'закрытой'}. Подтвердите создание мероприятия или отмените.",
            reply_markup=reply_markup)
    elif callback_data == 'confirm_event':
        # сохранение данных в бд
        save_event_to_db(user_id, user_event_data)
        await query.edit_message_text("*Джессика счастлива, мероприятие успешно создано*")
        event_data.pop(user_id, None)
        context.user_data.clear()
    elif callback_data == 'cancel_event':
        event_data.pop(user_id, None)
        context.user_data.clear()
        await query.edit_message_text("*Вы потеряли доверие Джессики, мероприятие отменено*")



def fetch_event_details(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return event

def format_event_details(event):
    return (f"Название: {event[2]}\n"
            f"Тематика: {event[3]}\n"
            f"Дресс-код: {event[4]}\n"
            f"Адрес: {event[5]}\n"
            f"Дата и время: {event[6]}\n"
            f"Тип: {'Открытая' if event[7] == 'open' else 'Закрытая'}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = (f"Привет, {user.first_name}! Меня зовут Джессика. Я главная тусовщича этого района!\n"
               "Готов начать вечеринку? Или присоединиться к вечеринке друзей?")
    buttons = [
        [InlineKeyboardButton("Помощь", callback_data='help')],
        [InlineKeyboardButton("Добавить мероприятие", callback_data='add_event')],
        [InlineKeyboardButton("Показать мероприятия", callback_data='show_events')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                                   reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Используйте следующие команды:\n"
                                    "/start - запустить бота\n"
                                    "/help - получить справку")


async def collect_event_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = context.user_data.get('state', '')

    if state == 'entering_name':
        event_data[user_id]['name'] = text
        await update.message.reply_text(f"Имя мероприятия установлено: {text}\nТеперь введите тематику мероприятия:")
        context.user_data['state'] = 'entering_theme'
    elif state == 'entering_theme':
        event_data[user_id]['theme'] = text
        await update.message.reply_text(f"Тематика мероприятия установлена: {text}\nВведите дресс-код мероприятия (или нажмите /skip для пропуска этого шага):")
        context.user_data['state'] = 'entering_dress_code'
    elif state == 'entering_dress_code':
        event_data[user_id]['dress_code'] = text
        await update.message.reply_text(f"Дресс-код установлен: {text}\nТеперь введите адрес мероприятия:")
        context.user_data['state'] = 'entering_address'
    elif state == 'entering_address':
        event_data[user_id]['address'] = text
        await update.message.reply_text(f"Адрес мероприятия установлен: {text}\nВыберите дату и время мероприятия (формат: ДД.ММ.ГГГГ ЧЧ:ММ):")
        context.user_data['state'] = 'entering_date_time'
    elif state == 'entering_date_time':
        event_data[user_id]['date_time'] = text
        buttons = [
            InlineKeyboardButton("Открытая вечеринка", callback_data='open_event'),
            InlineKeyboardButton("Закрытая вечеринка", callback_data='private_event')
        ]
        reply_markup = InlineKeyboardMarkup([buttons])
        await update.message.reply_text("Установите тип вечеринки:", reply_markup=reply_markup)
        context.user_data['state'] = 'choosing_type'

    # ДОБАВИТЬ ЛОГИКУ ПРИГЛАШЕНИЙ НА ЗАКРЫТУЮ ВЕЧЕРИНКУ

async def skip_dress_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    event_data[user_id]['dress_code'] = "Не указан"
    await update.message.reply_text(f"Дресс-код пропущен.\nТеперь введите адрес мероприятия:")
    context.user_data['state'] = 'entering_address'

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('skip', skip_dress_code))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_event_info))
    application.run_polling()

if __name__ == '__main__':
    main()
