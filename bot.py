from telegram import CallbackQuery, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from bot_static import (DAY_KEYBOARD, HOUR_TYPE_KEYBOARD, PORT, SELECT_TYPE, TIME, TYPE, get_hour_keyboard, logger,
                        query_teacher_handler, teacher_handler)
from core import Days, Teacher, conn, days, hour_types, hours
from core_static import HourType


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    with conn.cursor() as cur:
        user = update.message.from_user
        cur.execute('SELECT id FROM teacher WHERE id = (%s)', (user.id,))
        exist = cur.fetchone()
        if not exist:
            cur.execute(
                'INSERT INTO teacher(id, fio, telegram) VALUES(%(id)s, %(fio)s, %(telegram)s)',
                {'id': user.id, 'fio': f'{user.first_name} {user.last_name}', 'telegram': user.username}
            )
            update.message.reply_text(f'О, новый пользователь, привет, {user.first_name} {user.last_name}')
            update.message.reply_text(f'🎆')
            conn.commit()
        else:
            update.message.reply_text('Привет')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def unknown(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text('Не известная команда.')


@teacher_handler
def free(update: Update, context: CallbackContext, teacher: Teacher) -> None:
    """Get free time."""
    week_info_str = teacher.get_week_info_string(HourType.СВОБОДНОЕ)
    update.message.reply_text(week_info_str)


@teacher_handler
def busy(update: Update, context: CallbackContext, teacher: Teacher) -> None:
    """Get busy time."""
    week_info_str = teacher.get_week_info_string(HourType.ЗАНЯТОЕ)
    update.message.reply_text(week_info_str)


@teacher_handler
def relax(update: Update, context: CallbackContext, teacher: Teacher) -> None:
    """Get relax time."""
    week_info_str = teacher.get_week_info_string(HourType.ОТДЫХ)
    update.message.reply_text(week_info_str)


# ========================= SELECT DAY START =================================
def start_select(update: Update, context: CallbackContext) -> int:
    """Choice of days, remember selected day"""
    user = update.message.from_user
    logger.info("Учительница начала выбирать день", user.first_name)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(f"Выбери день", reply_markup=DAY_KEYBOARD)
    return TIME


@query_teacher_handler
def select_day(update: Update, context: CallbackContext, query: CallbackQuery, teacher: Teacher) -> int:
    """Choice of hours, remember selected day"""
    # Смотрим какой день был выбран, записываем в БД по ид учителя.
    selected_day_str = update.callback_query.data
    selected_day_int = [d.value.title() for d in Days].index(selected_day_str) + 1

    teacher.selected_day = selected_day_int
    HOUR_KEYBOARD = get_hour_keyboard()
    query.edit_message_text(text=f"Выбери время.\n{selected_day_str}.", reply_markup=HOUR_KEYBOARD)
    return TIME


@query_teacher_handler
def select_hour(update: Update, context: CallbackContext, query: CallbackQuery, teacher: Teacher) -> int:
    """Choice of type, remember selected hour"""
    selected_time = sorted((teacher.selected_time or []) + [update.callback_query.data])
    HOUR_KEYBOARD = get_hour_keyboard(selected_time)
    selected_day_str = tuple(d.value.title() for d in Days)[teacher.selected_day - 1]
    query.edit_message_text(
        text=f"Выбери еще время или продолжи дальше.\n{selected_day_str} - {selected_time}.",
        reply_markup=HOUR_KEYBOARD
    )
    teacher.selected_time = selected_time
    return TIME


@query_teacher_handler
def change_regime(update: Update, context: CallbackContext, query: CallbackQuery, teacher: Teacher) -> int:
    """Change regime of select type"""
    selected_day_str = tuple(d.value.title() for d in Days)[teacher.selected_day - 1]
    select_time = teacher.selected_time
    query.edit_message_text(
        text=f"Выбери тип.\n{selected_day_str} - {select_time}.", reply_markup=HOUR_TYPE_KEYBOARD
    )
    return TYPE


@query_teacher_handler
def select_type(update: Update, context: CallbackContext, query: CallbackQuery, teacher: Teacher) -> int:
    """
    Remember selected hour
    Return `ConversationHandler.END`, which tells the ConversationHandler that the conversation is over.
    """
    type_hour_dict = {hour_type.name.title(): hour_type.value for hour_type in HourType}
    selected_type_str = update.callback_query.data
    selected_type_int = type_hour_dict[selected_type_str]

    teacher.selected_type = selected_type_int

    selected_day, selected_time = teacher.selected_day, teacher.selected_time
    selected_day_str = tuple(d.value.title() for d in Days)[selected_day-1]

    query.edit_message_text(text=f"День:{selected_day_str}\nЧас:{selected_time}\nТип:{selected_type_str}")

    teacher.update_week_info(selected_day, selected_time, selected_type_int)
    return ConversationHandler.END
# ========================= SELECT DAY END =================================


def main() -> None:
    """Start the bot."""
    with open('private.key', 'r') as private_key:
        token = private_key.read()
        updater = Updater(token=token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # ^ means "start of line/string". $ means "select_type of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('day', start_select)],
        states={
            TIME: [
                CallbackQueryHandler(select_day, pattern=lambda x: x in days()),
                CallbackQueryHandler(select_hour, pattern=lambda x: x in hours()),
                CallbackQueryHandler(change_regime, pattern=f'^{SELECT_TYPE}$'),
                CallbackQueryHandler(select_type, pattern=lambda x: x in hour_types()),
            ],
            TYPE: [
                CallbackQueryHandler(select_type, pattern=lambda x: x in hour_types()),
            ]
        },
        fallbacks=[CommandHandler('day', start_select)],
    )

    # Add ConversationHandler to dispatcher that will be used for handling updates
    dispatcher.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("relax", relax))
    dispatcher.add_handler(CommandHandler("busy", busy))
    dispatcher.add_handler(CommandHandler("free", free))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, unknown))

    # Start the Bot
    # updater.start_polling() 447561995:AAEAOQPLeCqAxJBqbMGD0KScse_Mv0zv8Pk
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=token,
                          webhook_url="https://rezeda.herokuapp.com/" + token)
    updater.idle()


if __name__ == '__main__':
    main()
