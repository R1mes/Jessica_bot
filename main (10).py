from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '7016214070:AAHNjgA557iMV4XdIu4N08uxk-NVgEDLrvU'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #привет и помощь
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
    #помощь
    await update.message.reply_text("Используйте следующие команды:\n"
                                    "/start - запустить бота\n"
                                    "/help - получить справку")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #кнопки
    query = update.callback_query
    await query.answer()
    if query.data == 'help':
        buttons = [
            [InlineKeyboardButton("Добавить мероприятие", callback_data='add_event')],
            [InlineKeyboardButton("Показать мероприятия", callback_data='show_events')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text="Используйте команды:\n"
                                           "- Чтобы организовать вписку, нажми 'Добавить мероприятие'.\n"
                                           "- Ищешь COOL тусовку??? нажми 'Показать мероприятия'.",
                                      reply_markup=reply_markup)
    elif query.data == 'add_event':
        await query.edit_message_text(text="Функция добавления мероприятия будет реализована позже.")
    elif query.data == 'show_events':
        await query.edit_message_text(text="Функция показа мероприятий будет реализована позже.")

def main() -> None:
    #запуск
    application = Application.builder().token(TOKEN).build()

    # добавление обработчиков команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()
