import calendar
import logging
import sys
import traceback
from datetime import datetime, date

import telegram
from telegram.utils.helpers import mention_html
from fastnumbers import fast_float
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ParseMode, \
    BotCommand
from telegram.ext import ConversationHandler
from telegram_bot_calendar import LSTEP

from bot.bot_utils import build_menu, MyStyleCalendar, add_new_expense, add_new_gain, get_chart_from_sheet, CURRENCY, \
    get_sheet_min_max_month, get_table_from_sheet, get_sheet_expenses, get_sheet_gains, delete_expense, delete_gain, \
    get_sheet_report, create_sheet_by_month
from env_variables import USER_ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

keyboard = ['💸 New Expense', '🤑 New Gain',
            '📈 Show Table', '📊 Show Graph',
            '🗑️💸 Delete Expense', '🗑️💰 Delete Gain',
            '📋 Show Report', '📃 New Sheet',
            '🔁 Set new Repeatable', '🗑🔁 Delete a Repeatable',
            '⁉ Help']
DATE, SET_CALENDAR, NAME, IMPORT, CHART_CALENDAR, CHART_DATE, DELETE_ELEMENT, NEW_SHEET_CALENDAR, NEW_SHEET_DATE, \
    ADD_SHEET = range(10)

COMMANDS = {
    'start': BotCommand('start', 'Start the bot'),
    'cancel': BotCommand('cancel', 'Abort current operation'),
    'add_expense': BotCommand('add_expense', 'Add a new expense in the sheet'),
    'add_gain': BotCommand('add_gain', 'Add a new gain in the sheet'),
    'show_table': BotCommand('show_table', 'Show the summary table of all the expenses and the gains'),
    'show_chart': BotCommand('show_chart', 'Show a pie chart relative to the expenses'),
    'delete_expense': BotCommand('delete_expense', 'Delete an expense from a sheet'),
    'delete_gain': BotCommand('delete_gain', 'Delete a gain from a sheet'),
    'show_report': BotCommand('show_report', 'Show the summary amounts of the month'),
    'new_sheet': BotCommand('new_sheet', 'Create a new monthly sheet in the spreadsheet'),
    'new_repeatable': BotCommand('new_repeatable', 'Add a new recurrent expense or gain when creating a new sheet'),
    'delete_repeatable': BotCommand('delete_repeatable', 'Delete a recurrent expense or gain'),
    'help': BotCommand('help', 'Get help for the bot usage')
}


def get_keyboard():
    return ReplyKeyboardMarkup(build_menu(keyboard[:-1], 2, footer_buttons=keyboard[-1]),
                               resize_keyboard=True,
                               one_time_keyboard=False)


def send_images_helper(context, chat_id, images, caption):
    """
    Helper for send images.
    If images list has one only element it will be send as single photo.
    If images list size is more than 1, then they will be send as album.
    """
    if len(images) > 1:
        media_photos = [InputMediaPhoto(image) for image in images]
        media_photos[0].caption = caption
        context.bot.send_media_group(chat_id=chat_id, media=media_photos, parse_mode=ParseMode.MARKDOWN)

    elif len(images) == 1:
        context.bot.send_photo(chat_id=chat_id, photo=images[0], caption=caption, parse_mode=ParseMode.MARKDOWN)


def not_allowed(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="User not allowed in this chat.")


def unknown(update, context):
    """ UNKNOWN COMMAND"""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.",
                             reply_markup=get_keyboard())


def start(update, context):
    """ COMMAND 'start' """
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="I'm the monthly expense tracker",
                             reply_markup=get_keyboard())


"""
    NEW ELEMENT START
"""


def new_element(update, context, command=None):
    context.user_data['element'] = keyboard.index(update.message.text if command is None else command)
    date_choose_keyboard = [[InlineKeyboardButton("👇 Today", callback_data='today'),
                             InlineKeyboardButton("📅 Calendar", callback_data='calendar')],
                            [InlineKeyboardButton('✖ Cancel', callback_data='cancel')]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='⚠ Insert the date of the element:',
                             reply_markup=InlineKeyboardMarkup(date_choose_keyboard))
    return DATE


"""
    NEW ELEMENT CHOOSE DATE
"""


def choose_date(update, context):
    query = update.callback_query

    if query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END

    min_, max_ = get_sheet_min_max_month()
    if query.data == 'today':
        today = date.today()
        if min_ <= today.month <= max_:
            context.user_data['date'] = date.today()
            query.edit_message_text(text=f"📆 Date: {date.today().strftime('%d/%m/%Y')}\n\n"
                                         f"✍ Insert the description\n\n"
                                         f"/{COMMANDS['cancel'].command}")
            return NAME
        else:
            query.edit_message_text(text=f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                                         f"📃 Create a new sheet for the selected month "
                                         f"with /{COMMANDS['new_sheet'].command} command")
            return ConversationHandler.END

    elif query.data == 'calendar':
        if min_ != -1 and max_ != -1:
            today = date.today()
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, calendar.monthrange(today.year, max_)[1])
            context.user_data['date_min_max'] = date_min, date_max
            cal, step = MyStyleCalendar(max_date=date_max, min_date=date_min).build()
            query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                    f"/{COMMANDS['cancel'].command}",
                                    reply_markup=cal)
            return SET_CALENDAR
        else:
            query.edit_message_text(text=f"⚠ Warning! No sheets are present.\n\n"
                                         f"📃 Create a new one with /{COMMANDS['new_sheet'].command} command")
            return ConversationHandler.END


"""
    NEW ELEMENT CHOOSE WITH CALENDAR
"""


def calendar_set(update, context):
    query = update.callback_query
    date_min, date_max = context.user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min).process(
        query.data)
    if not result and key:
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/{COMMANDS['cancel'].command}",
                                reply_markup=key)
        return SET_CALENDAR
    elif result:
        context.user_data['date'] = result
        query.edit_message_text(text=f"📆 Date: {result.strftime('%d/%m/%Y')}\n\n"
                                     f"✍ Insert the description\n\n"
                                     f"/{COMMANDS['cancel'].command}")
        return NAME


"""
    NEW ELEMENT ADD NAME
"""


def add_name(update, context):
    logger.info('Date selected: %s', context.user_data)
    context.user_data['name'] = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"📆 Date: {context.user_data['date'].strftime('%d/%m/%Y')}\n\n"
                                  f"✍ Description: {context.user_data['name']}\n\n"
                                  "💰 Add the amount\n\n"
                                  f"/{COMMANDS['cancel'].command}")
    return IMPORT


"""
    NEW ELEMENT ADD IMPORT
"""


def add_import(update, context):
    message = update.message.text
    amount = round(fast_float(message, default=-1), 2)
    if amount == -1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="⚠ The amount is not correct! "
                                      "Only numbers with 2 decimal are allowed\n\n"
                                      f"/{COMMANDS['cancel'].command}")
        return IMPORT

    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=telegram.ChatAction.TYPING)
    logger.info('User Data: %s %s', context.user_data, amount)
    if context.user_data['element'] == 0:
        updated = add_new_expense(context.user_data['date'], context.user_data['name'], amount)
    elif context.user_data['element'] == 1:
        updated = add_new_gain(context.user_data['date'], context.user_data['name'], amount)
    else:
        updated = 0

    if updated > 0:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"✅ New element added!\n\n"
                                      f"📆 Date: {context.user_data['date'].strftime('%d/%m/%Y')}\n"
                                      f"✍ Description: {context.user_data['name']}\n"
                                      f"💰 Amount: {CURRENCY}{amount}\n")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"⚠ Element not added, retry!")
    return ConversationHandler.END


"""
    TABLE, CHART, DELETE ELEMENT START
"""


def get_chart_date(update, context, command=None):
    index = keyboard.index(update.message.text if command is None else command)
    context.user_data['element'] = index
    date_choose_keyboard = [[InlineKeyboardButton("👇 This Month", callback_data='this_month'),
                             InlineKeyboardButton("📅 Calendar", callback_data='calendar')],
                            [InlineKeyboardButton('✖ Cancel', callback_data='cancel')]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='⚠ Select the month of the sheet:',
                             reply_markup=InlineKeyboardMarkup(date_choose_keyboard))
    return NEW_SHEET_CALENDAR if index == 7 else CHART_CALENDAR


"""
    TABLE, CHART, DELETE ELEMENT CHOOSE DATE
"""


def chart_calendar(update, context):
    query = update.callback_query
    if query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END

    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if query.data == 'this_month':
        if min_ <= today.month <= max_:
            return __get_chart_or_table(update, context, today, query)
        else:
            query.edit_message_text(text=f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                                         f"📃 Create a new sheet for the selected month "
                                         f"with /{COMMANDS['new_sheet'].command} command")
            return ConversationHandler.END

    elif query.data == 'calendar':
        if min_ != -1 and max_ != -1:
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, calendar.monthrange(today.year, max_)[1])
            context.user_data['date_min_max'] = date_min, date_max
            cal = MyStyleCalendar(max_date=date_max, min_date=date_min)
            cal.first_step = 'm'
            cal, step = cal.build()
            query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                    f"/{COMMANDS['cancel'].command}",
                                    reply_markup=cal)
            return CHART_DATE
        else:
            query.edit_message_text(text=f"⚠ Warning! No sheets are present.\n\n"
                                         f"📃 Create a new one with /{COMMANDS['new_sheet'].command} command")
            return ConversationHandler.END


"""
    TABLE, CHART, DELETE ELEMENT CHOOSE FROM CALENDAR
"""


def set_chart_date(update, context):
    query = update.callback_query
    date_min, date_max = context.user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min).process(query.data)
    if step == 'm' and key:
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/{COMMANDS['cancel'].command}",
                                reply_markup=key)
        return NEW_SHEET_DATE if context.user_data['element'] == 7 else CHART_DATE
    elif step == 'd':
        params = query.data.split("_")
        params = dict(
            zip(["start", "calendar_id", "action", "step", "year", "month", "day"][:len(params)], params))
        month = int(params["month"])
        today = datetime.today()
        today = date(today.year, month, today.day)
        return __create_new_sheet(update, context, today, query) \
            if context.user_data['element'] == 7 \
            else __get_chart_or_table(update, context, today, query)


# DELETE RESPONSE
def delete_element(update, context):
    query = update.message.text
    if query == '✖ Cancel':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='👍 Cancelled.',
                                 reply_markup=get_keyboard())
    else:
        values = context.user_data['values']
        try:
            index = values.index(query)
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='❗ Element not recognized. '
                                          'Use the keyboard buttons to select the element to remove')
            return DELETE_ELEMENT

        deleting_mess = context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text='🔄 Deleting...')
        context.bot.sendChatAction(chat_id=update.effective_chat.id,
                                   action=telegram.ChatAction.TYPING)
        date_ = context.user_data['date']

        if context.user_data['element'] == 4:
            delete_expense(date_, index)
        elif context.user_data['element'] == 5:
            delete_gain(date_, index)

        context.bot.delete_message(chat_id=update.effective_chat.id,
                                   message_id=deleting_mess.message_id)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='👍 Element deleted',
                                 reply_markup=get_keyboard())
    return ConversationHandler.END


# DELETE SECTION
def __delete_element(update, context, date_, query):
    query.edit_message_text(text='🔄 Retrieving data...')
    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=telegram.ChatAction.TYPING)
    context.user_data['date'] = date_
    # delete expense
    if context.user_data['element'] == 4:
        values = get_sheet_expenses(date_)
        if len(values) > 0:
            values = [' '.join(x) for x in values]
            context.user_data['values'] = values
            keys = ReplyKeyboardMarkup(build_menu(values, 1, header_buttons='✖ Cancel'),
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=query.message.message_id)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='📛 Choose the expense to remove',
                                     reply_markup=keys)
            return DELETE_ELEMENT
        else:
            query.edit_message_text(
                text=f'⚠ No expense found, add new one with /{COMMANDS["add_expense"].command} command')

    # delete gain
    elif context.user_data['element'] == 5:
        values = get_sheet_gains(date_)
        if len(values) > 0:
            values = [' '.join(x) for x in values]
            context.user_data['values'] = values
            keys = ReplyKeyboardMarkup(build_menu(values, 1, header_buttons='✖ Cancel'),
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='📛 Choose the gain to remove',
                                     reply_markup=keys)
            return DELETE_ELEMENT
        else:
            query.edit_message_text(text=f'⚠ No gain found, add new one with /{COMMANDS["add_gain"].command} command')
    return ConversationHandler.END


# SHOW REPORT
def __show_report(update, context, date_, query):
    query.edit_message_text(text='🔄 Retrieving data...')
    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=telegram.ChatAction.TYPING)
    surplus, gains, expenses = get_sheet_report(date_)
    query.edit_message_text(text=f'💹 Report for {date_.strftime("%B")}\n\n'
                                 f'💰  TOTAL GAINS: {gains}\n\n'
                                 f'💸  TOTAL EXPENSE: {expenses}\n\n'
                                 f'🤑  SURPLUS: {surplus}')


# CHART, TABLE SECTION
def __get_chart_or_table(update, context, date_, query):
    chart_date = date_
    # get table
    if context.user_data['element'] == 2:
        query.edit_message_text(text='🔄 Retrieving the table...')
        context.bot.sendChatAction(chat_id=update.effective_chat.id,
                                   action=telegram.ChatAction.UPLOAD_PHOTO)
        image = get_table_from_sheet(chart_date)
        caption = f'Summary Table for {chart_date.strftime("%B")}'
    # get chart
    elif context.user_data['element'] == 3:
        query.edit_message_text(text='🔄 Retrieving the chart...')
        context.bot.sendChatAction(chat_id=update.effective_chat.id,
                                   action=telegram.ChatAction.UPLOAD_PHOTO)
        image = get_chart_from_sheet(chart_date)
        caption = f'Expanses Pie Chart for {chart_date.strftime("%B")}'
    # show report
    elif context.user_data['element'] == 6:
        return __show_report(update, context, date_, query)
    # delete element
    else:
        return __delete_element(update, context, date_, query)

    if image is None:
        query.edit_message_text(text='⚠ No data found to create the table')
    else:
        send_images_helper(context, update.effective_chat.id, [image], caption=caption)
    return ConversationHandler.END


"""
    NEW SHEET CALENDAR
"""


def __create_new_sheet(update, context, date_, query):
    query.edit_message_text(text='🔄 Creating a new sheet...')
    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=telegram.ChatAction.TYPING)
    create_sheet_by_month(date_)
    query.edit_message_text(text=f'👍 New sheet created for the month {date_.strftime("%B")}')
    return ConversationHandler.END


def new_sheet_date_choose(update, context):
    query = update.callback_query
    if query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END

    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if query.data == 'this_month':
        if today.month > max_:
            return __create_new_sheet(update, context, today, query)
        else:
            if max_ < 12:
                query.edit_message_text(text=f"⚠ Warning! The month '{today.strftime('%B')}' is already present.\n\n"
                                             f"📃 Create a new expense or a new gain "
                                             f"with /{COMMANDS['add_expense'].command} "
                                             f"or /{COMMANDS['add_gain'].command} command")
            else:
                query.edit_message_text(text=f"⚠ This spreadsheet is full, create a new one in Google Spreadsheet"
                                             f"and set the new SPREADSHEET_ID environment variable\n\n")

    elif query.data == 'calendar':
        if max_ < 12:
            date_min = date(today.year, max_ + 1, 1)
            date_max = date(today.year, 12, 31)
            context.user_data['date_min_max'] = date_min, date_max
            cal = MyStyleCalendar(max_date=date_max, min_date=date_min)
            cal.first_step = 'm'
            cal, step = cal.build()
            query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                    f"/{COMMANDS['cancel'].command}",
                                    reply_markup=cal)
            return NEW_SHEET_DATE
        else:
            query.edit_message_text(text=f"⚠ This spreadsheet is full, create a new one in Google Spreadsheet"
                                         f"and set the new SPREADSHEET_ID environment variable\n\n")

    return ConversationHandler.END


"""
    CANCEL COMMAND
"""


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='❌ Cancelled')
    return ConversationHandler.END


"""
    ERROR HANDLER FUNCTION
"""


def error(update, context):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    # This is a personal bot, so the user is also the dev
    devs = [USER_ID]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message
    # could fail
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML, reply_markup=get_keyboard())
    raise
