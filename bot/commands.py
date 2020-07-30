import logging
from datetime import datetime, date

import telegram
from fastnumbers import fast_float
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, ParseMode
from telegram.ext import ConversationHandler
from telegram_bot_calendar import LSTEP

from bot.bot_utils import build_menu, MyStyleCalendar, add_new_expense, add_new_gain, get_chart_from_sheet, CURRENCY

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
    if query.data == 'today':
        context.user_data['date'] = date.today()
        query.edit_message_text(text=f"📆 Date: {date.today().strftime('%d/%m/%Y')}\n\n"
                                     f"✍ Insert the description\n\n"
                                     f"/cancel")
        return NAME
    elif query.data == 'calendar':
        # TODO check the sheets before to disable the month not available
        today = date.today()
        cal, step = MyStyleCalendar(max_date=date(today.year, 12, 31), min_date=date(today.year, 1, 1)).build()
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=cal)
        return SET_CALENDAR
    elif query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END


def calendar(update, context):
    query = update.callback_query
    # TODO see above
    today = date.today()
    result, key, step = MyStyleCalendar(max_date=date(today.year, 12, 31), min_date=date(today.year, 1, 1)).process(
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
    if query.data == 'this_month':
        return __get_chart(update, context, date.today(), query)

    elif query.data == 'calendar':
        today = date.today()
        cal = MyStyleCalendar(max_date=today, min_date=date(today.year, 1, 1))
        cal.first_step = 'm'
        cal, step = cal.build()
        query.edit_message_text(f"👉 Select {LSTEP[step]}\n\n"
                                f"/cancel",
                                reply_markup=cal)
        return CHART_DATE
    elif query.data == 'cancel':
        query.edit_message_text(text='❌ Cancelled')
        return ConversationHandler.END


def set_chart_date(update, context):
    query = update.callback_query
    result, key, step = MyStyleCalendar().process(query.data)
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
