import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from core import Teacher, days, hour_types, hours

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get('PORT', '8443'))

# Stages
TIME, TYPE = range(2)

SELECT_TYPE = 'Выбрать занятость ⏭'

DAY_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton(day, callback_data=day)] for day in days()])
HOUR_TYPE_KEYBOARD = InlineKeyboardMarkup([[InlineKeyboardButton(type, callback_data=type)] for type in hour_types()])


def get_hour_keyboard(selected_time: list[str] | None = None) -> InlineKeyboardMarkup:
    selected_time = set(selected_time) if selected_time else set()
    buttons = sorted(set(hours()) - selected_time | ({SELECT_TYPE} if selected_time else set()))
    return InlineKeyboardMarkup([[InlineKeyboardButton(button, callback_data=button)] for button in buttons])


def query_teacher_handler(handler_func):
    def wrapper(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        id = update.effective_user.id
        teacher = Teacher(id)
        handler_func(update, context, query, teacher)
    return wrapper


def teacher_handler(handler_func):
    def wrapper(update: Update, context: CallbackContext):
        teacher = Teacher(update.effective_user.id)
        handler_func(update, context, teacher)
    return wrapper
