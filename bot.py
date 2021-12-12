import logging

from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
)
import os
PORT = int(os.environ.get('PORT', '8443'))

from core import Rezeda

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Stages
TIME, TYPE = range(2)


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(Rezeda().get_info())


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def unknow(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text('Не известная команда.')


def select_day(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [
        [InlineKeyboardButton(day, callback_data=day)] for day in Rezeda().days
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(f"Выбери день", reply_markup=reply_markup)
    return TIME


def select_hour(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton(hour, callback_data=hour)] for hour in Rezeda().hours
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    Rezeda.selected_day = update.callback_query.data
    query.edit_message_text(
        text=f"Выбери время.\n{Rezeda.selected_day}.", reply_markup=reply_markup
    )
    return TIME


def select_type(update: Update, context: CallbackContext) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton(type, callback_data=type)] for type in ['Занято', 'Отдых', 'Свободно']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    Rezeda.selected_hour = update.callback_query.data
    query.edit_message_text(
        text=f"Выбери тип.\n{Rezeda.selected_day} - {Rezeda.selected_hour}.", reply_markup=reply_markup
    )
    # Transfer to conversation state `SECOND`
    return TYPE


def end(update: Update, context: CallbackContext) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    query.answer()
    Rezeda.selected_type = {'Занято': 1, 'Отдых': 2, 'Свободно': 0}.get(update.callback_query.data)
    query.edit_message_text(
        text=f"День:{Rezeda.selected_day}\nЧас:{Rezeda.selected_hour}\nТип:{update.callback_query.data}"
    )
    Rezeda().update_week_info(Rezeda.selected_day, Rezeda.selected_hour, Rezeda.selected_type)
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    with open('private.key', 'r') as private_key:
        token = private_key.read()
        updater = Updater(token=token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('day', select_day)],
        states={
            TIME: [
                CallbackQueryHandler(select_hour, pattern=lambda x: x in Rezeda().days),
                CallbackQueryHandler(select_type, pattern=lambda x: x in Rezeda().hours),
            ],
            TYPE: [
                CallbackQueryHandler(end, pattern=lambda x: x in ['Занято', 'Отдых', 'Свободно']),
            ]
        },
        fallbacks=[CommandHandler('day', select_day)],
    )

    # Add ConversationHandler to dispatcher that will be used for handling updates
    dispatcher.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, unknow))

    # Start the Bot
    # updater.start_polling()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=token,
                          webhook_url="https://rezeda.herokuapp.com/" + token)
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
