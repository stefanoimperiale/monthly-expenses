import logging
import sys
import traceback
from datetime import datetime, date

import telegram
from telegram.utils.helpers import mention_html
from fastnumbers import fast_float
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ParseMode
from telegram.ext import ConversationHandler
from telegram_bot_calendar import LSTEP

from bot.bot_utils import build_menu, MyStyleCalendar, add_new_expense, add_new_gain, get_chart_from_sheet, CURRENCY, \
    USER_ID, get_sheet_min_max_month

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
keyboard = ['💸 New Expense', '🤑 New Gain', '📈 Show Table', '📊 Show Graph', '📃 New Sheet', '⁉ Help']
DATE, SET_CALENDAR, NAME, IMPORT, CHART_CALENDAR, CHART_DATE = range(6)


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


def new_element(update, context):
    context.user_data['element'] = keyboard.index(update.message.text)
    date_choose_keyboard = [[InlineKeyboardButton("👇 Today", callback_data='today'),
                             InlineKeyboardButton("📅 Calendar", callback_data='calendar')],
                            [InlineKeyboardButton('✖ Cancel', callback_data='cancel')]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='⚠ Insert the date of the element:',
                             reply_markup=InlineKeyboardMarkup(date_choose_keyboard))
    return DATE


def choose_date(update, context):
    query = update.callback_query
    min_, max_ = get_sheet_min_max_month()
    if query.data == 'today':
        today = date.today()
        if min_ <= today.month <= max_:
            context.user_data['date'] = date.today()
            query.edit_message_text(text=f"📆 Date: {date.today().strftime('%d/%m/%Y')}\n\n"
                                         f"✍ Insert the description\n\n"
                                         f"/cancel")
            return NAME
        else:
            query.edit_message_text(text=f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                                         f"📃 Create a new sheet for the selected month with /new_sheet command")
            return ConversationHandler.END

    elif query.data == 'calendar':
        if min_ != -1 and max_ != -1:
            today = date.today()
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, 31)
            context.user_data['date_min_max'] = date_min, date_max
            cal, step = MyStyleCalendar(max_date= date_max, min_date=date_min).build()
            query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                    f"/cancel",
                                    reply_markup=cal)
            return SET_CALENDAR
        else:
            query.edit_message_text(text=f"⚠ Warning! No sheets are present.\n\n"
                                         f"📃 Create a new one with /new_sheet command")
            return ConversationHandler.END
    elif query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END


def calendar(update, context):
    query = update.callback_query
    date_min, date_max = context.user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min).process(
        query.data)
    if not result and key:
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=key)
        return SET_CALENDAR
    elif result:
        context.user_data['date'] = result
        query.edit_message_text(text=f"📆 Date: {result.strftime('%d/%m/%Y')}\n\n"
                                     f"✍ Insert the description\n\n"
                                     f"/cancel")
        return NAME


def add_name(update, context):
    logger.info('Date selected: %s', context.user_data)
    context.user_data['name'] = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"📆 Date: {context.user_data['date'].strftime('%d/%m/%Y')}\n\n"
                                  f"✍ Description: {context.user_data['name']}\n\n"
                                  "💰 Add the amount\n\n"
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


def get_chart_date(update, context):
    date_choose_keyboard = [[InlineKeyboardButton("👇 This Month", callback_data='this_month'),
                             InlineKeyboardButton("📅 Calendar", callback_data='calendar')],
                            [InlineKeyboardButton('✖ Cancel', callback_data='cancel')]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='⚠ Select the month of the chart:',
                             reply_markup=InlineKeyboardMarkup(date_choose_keyboard))
    return CHART_CALENDAR


def chart_calendar(update, context):
    query = update.callback_query
    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if query.data == 'this_month':
        if min_ <= today.month <= max_:
            return __get_chart(update, context, today, query)
        else:
            query.edit_message_text(text=f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                                         f"📃 Create a new sheet for the selected month with /new_sheet command")
            return ConversationHandler.END

    elif query.data == 'calendar':
        if min_ != -1 and max_ != -1:
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, 31)
            context.user_data['date_min_max'] = date_min, date_max
            cal = MyStyleCalendar(max_date=date_max, min_date=date_min)
            cal.first_step = 'm'
            cal, step = cal.build()
            query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                    f"/cancel",
                                    reply_markup=cal)
            return CHART_DATE
        else:
            query.edit_message_text(text=f"⚠ Warning! No sheets are present.\n\n"
                                         f"📃 Create a new one with /new_sheet command")
            return ConversationHandler.END
    elif query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END


def set_chart_date(update, context):
    query = update.callback_query
    date_min, date_max = context.user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min).process(query.data)
    if step == 'm' and key:
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=key)
        return CHART_DATE
    elif step == 'd':
        params = query.data.split("_")
        params = dict(
            zip(["start", "calendar_id", "action", "step", "year", "month", "day"][:len(params)], params))
        month = int(params["month"])
        today = datetime.today()
        today = date(today.year, month, today.day)
        return __get_chart(update, context, today, query)


def __get_chart(update, context, date_, query):
    query.edit_message_text(text='🔄 Retrieving the chart...')
    context.bot.sendChatAction(chat_id=update.effective_chat.id,
                               action=telegram.ChatAction.UPLOAD_PHOTO)
    chart_date = date_
    image = get_chart_from_sheet(chart_date)
    send_images_helper(context, update.effective_chat.id, [image],
                       f'Expanses Pie Chart for {chart_date.strftime("%B")}')
    return ConversationHandler.END


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='❌ Cancelled')
    return ConversationHandler.END


# Error handler function
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
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    raise
