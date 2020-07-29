import logging
from datetime import datetime, date

from fastnumbers import fast_float
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram_bot_calendar import LSTEP

from bot.bot_utils import build_menu, MyStyleCalendar, add_new_sheet_element

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
keyboard = ['💸 New Expanse', '🤑 New Gain', '📊 Show Report', '📆 Set Month']
DATE, SET_CALENDAR, NAME, IMPORT = range(4)


def get_keyboard():
    return ReplyKeyboardMarkup(build_menu(keyboard, 2),
                               resize_keyboard=True,
                               one_time_keyboard=False)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def unknown(update, context):
    """ UNKNOWN COMMAND"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.",
                             reply_markup=get_keyboard())


def start(update, context):
    """ COMMAND 'start' """
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="I'm the monthly expanses planner",
                             reply_markup=get_keyboard())


def new_element(update, context):
    context.user_data['element'] = update.message.text
    date_choose_keyboard = [[InlineKeyboardButton("👇 Today", callback_data='today'),
                             InlineKeyboardButton("📅 Calendar", callback_data='calendar')],
                            [InlineKeyboardButton('✖ Cancel', callback_data='cancel')]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='⚠ Insert the date of the element:',
                             reply_markup=InlineKeyboardMarkup(date_choose_keyboard))
    return DATE


def choose_date(update, context):
    query = update.callback_query
    if query.data == 'today':
        context.user_data['date'] = date.today()
        query.edit_message_text(text=f"📆 Select {date.today().strftime('%d/%m/%Y')}\n\n"
                                     f"✍ Insert the description\n\n"
                                     f"/cancel")
        return NAME
    elif query.data == 'calendar':
        cal, step = MyStyleCalendar().build()
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=cal)
        return SET_CALENDAR
    elif query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END


def calendar(update, context):
    query = update.callback_query
    result, key, step = MyStyleCalendar().process(query.data)
    if not result and key:
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=key)
        return SET_CALENDAR
    elif result:
        context.user_data['date'] = result
        query.edit_message_text(text=f"📆 Select {result.strftime('%d/%m/%Y')}\n\n"
                                     f"✍ Insert the description\n\n"
                                     f"/cancel")
        return NAME


def add_name(update, context):
    logger.info('Date selected: %s', context.user_data)
    context.user_data['name'] = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="💰 Add the amount\n\n"
                                  "/cancel")
    return IMPORT


def add_import(update, context):
    message = update.message.text
    amount = round(fast_float(message, default=-1), 2)
    if amount == -1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="⚠ The amount is not correct! "
                                      "Only numbers with 2 decimal are allowed\n\n"
                                      "/cancel")
        return IMPORT
    logger.info('User Data: %s %s', context.user_data, amount)
    updated = add_new_sheet_element(context.user_data['date'], context.user_data['name'], amount)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"✅ New element added {updated}")
    return ConversationHandler.END


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='❌ Cancelled')
    return ConversationHandler.END
