import calendar
import html
import sys
import traceback
from datetime import datetime, date

from fastnumbers import fast_float
from telegram_bot_calendar import LSTEP
from telethon import types, Button, events

from app.bot.bot_utils import build_menu, MyStyleCalendar, add_new_expense, add_new_earning, get_chart_from_sheet, \
    get_sheet_min_max_month, get_table_from_sheet, get_sheet_expenses, get_sheet_earnings, delete_expense, \
    delete_earning, get_sheet_report, create_sheet_by_month, add_recurrent, get_recurrent_elements, remove_recurrent, \
    get_user_id
from app.client import client, user_data, BotState, conversation_end
from app.env_variables import USER_ID, CURRENCY, logger

COMMANDS = {
    'start': types.BotCommand(
        command='start',
        description='Start the bot'
    ),
    'cancel': types.BotCommand(
        command='cancel',
        description='Abort current operation'
    ),
    'add_expense': types.BotCommand(
        command='add_expense',
        description='Add a new expense in the sheet'
    ),
    'add_earning': types.BotCommand(
        command='add_earning',
        description='Add a new earning in the sheet'
    ),
    'show_table': types.BotCommand(
        command='show_table',
        description='Show the summary table of all the expenses and the earnings'
    ),
    'show_chart': types.BotCommand(
        command='show_chart',
        description='Show a pie chart relative to the expenses'
    ),
    'delete_expense': types.BotCommand(
        command='delete_expense',
        description='Delete an expense from a sheet'
    ),
    'delete_earning': types.BotCommand(
        command='delete_earning',
        description='Delete a earning from a sheet'
    ),
    'show_report': types.BotCommand(
        command='show_report',
        description='Show the summary amounts of the month'
    ),
    'new_sheet': types.BotCommand(
        command='new_sheet',
        description='Create a new monthly sheet in the spreadsheet'
    ),
    'new_recurrent': types.BotCommand(
        command='new_recurrent',
        description='Add a new recurrent expense or earning when creating a new sheet'
    ),
    'delete_recurrent': types.BotCommand(
        command='delete_recurrent',
        description='Delete a recurrent expense or earning'
    ),
    'help': types.BotCommand(
        command='help',
        description='Get help for the bot usage'
    )
}

keyboard = {
    'new_expense': Button.text('💸 New Expense', resize=True, single_use=True),
    'new_earning': Button.text('🤑 New Earning', resize=True, single_use=True),
    'show_table': Button.text('📈 Show Table', resize=True, single_use=True),
    'show_graph': Button.text('📊 Show Chart', resize=True, single_use=True),
    'delete_expense': Button.text('🗑️💸 Delete Expense', resize=True, single_use=True),
    'delete_earning': Button.text('🗑️💰 Delete Earning', resize=True, single_use=True),
    'show_report': Button.text('📋 Show Report', resize=True, single_use=True),
    'new_sheet': Button.text('📃 New Sheet', resize=True, single_use=True),
    'new_recurrent': Button.text('🔁 Set new Recurrent', resize=True, single_use=True),
    'delete_recurrent': Button.text('🗑🔁 Delete a Recurrent', resize=True, single_use=True),
    'help': Button.text('⁉ Help', resize=True, single_use=True)
}
keyboard_list = list(keyboard.values())
keyboard_test_list = list(map(lambda x: x.button.text, keyboard.values()))


def get_keyboard():
    return client.build_reply_markup(build_menu(keyboard_list[:-1], 2, footer_buttons=keyboard_list[-1]),
                                     )


async def send_images_helper(user_id, images, caption):
    """
    Helper for send images.
    If images list has one only element it will be send as single photo.
    If images list size is more than 1, then they will be send as album.
    """
    await client.send_file(user_id, images, caption=caption, force_document=False, parse_mode='markdown')


async def not_allowed(update):
    user_id = get_user_id(update)
    await client.send_message(user_id, "User not allowed in this chat.")


async def unknown(update):
    """ UNKNOWN COMMAND"""
    user_id = get_user_id(update)
    await client.send_message(user_id, "Sorry, I didn't understand that command.",
                              buttons=get_keyboard())


async def start(update):
    """ COMMAND 'start' """
    user_id = get_user_id(update)
    await client.send_message(user_id,
                              "I'm the monthly expense tracker",
                              buttons=get_keyboard())


"""
    NEW ELEMENT START
"""


async def new_element(update, command):
    user_id = get_user_id(update)
    user_data['element'] = command
    date_choose_keyboard = [[Button.inline("👇 Today", data='today'),
                             Button.inline("📅 Calendar", data='calendar')],
                            [Button.inline('✖ Cancel', data='cancel')]]
    await client.send_message(user_id,
                              '⚠ Insert the date of the element:',
                              buttons=date_choose_keyboard)
    return BotState.DATE


"""
    NEW ELEMENT CHOOSE DATE
"""


async def choose_date(update):
    query = update.data.decode('utf-8')

    if query == 'cancel':
        await update.edit('❌ Cancelled')
        conversation_end(update)
        return None

    min_, max_ = get_sheet_min_max_month()
    if query == 'today':
        today = date.today()
        if min_ <= today.month <= max_:
            user_data['date'] = date.today()
            await update.edit(f"📆 Date: {date.today().strftime('%d/%m/%Y')}\n\n"
                              f"✍ Insert the description\n\n"
                              f"/{COMMANDS['cancel'].command}")
            return BotState.NAME
        else:
            await update.edit(f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                              f"📃 Create a new sheet for the selected month "
                              f"with /{COMMANDS['new_sheet'].command} command")
            conversation_end(update)
            return None

    elif query == 'calendar':
        if min_ != -1 and max_ != -1:
            today = date.today()
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, calendar.monthrange(today.year, max_)[1])
            user_data['date_min_max'] = date_min, date_max
            cal, step = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True).build()
            await update.edit(f"👉 Select {LSTEP[step]}\n\n"
                              f"/{COMMANDS['cancel'].command}",
                              buttons=cal)
            return BotState.SET_CALENDAR
        else:
            await update.edit(f"⚠ Warning! No sheets are present.\n\n"
                              f"📃 Create a new one with /{COMMANDS['new_sheet'].command} command")
            conversation_end(update)
            return None


"""
    NEW ELEMENT CHOOSE WITH CALENDAR
"""


async def calendar_set(update):
    query = update.data.decode('utf-8')
    date_min, date_max = user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True).process(query)
    if not result and key:
        await update.edit(f"👉 Select {LSTEP[step]}\n\n"
                          f"/{COMMANDS['cancel'].command}",
                          buttons=key)
        return BotState.SET_CALENDAR
    elif result:
        user_data['date'] = result
        await update.edit(f"📆 Date: {result.strftime('%d/%m/%Y')}\n\n"
                          f"✍ Insert the description\n\n"
                          f"/{COMMANDS['cancel'].command}")
        return BotState.NAME


"""
    NEW ELEMENT ADD NAME
"""


async def add_name(update):
    user_id = get_user_id(update)
    logger.info('Date selected: %s', user_data)
    user_data['name'] = update.message.text
    await client.send_message(user_id,
                              f"📆 Date: {user_data['date'].strftime('%d/%m/%Y')}\n\n"
                              f"✍ Description: {user_data['name']}\n\n"
                              "💰 Add the amount\n\n"
                              f"/{COMMANDS['cancel'].command}")
    return BotState.IMPORT


"""
    NEW ELEMENT ADD IMPORT
"""


async def add_import(update):
    user_id = get_user_id(update)
    message = update.message.text
    amount = round(fast_float(message, default=-1), 2)
    if amount == -1:
        await client.send_message(user_id,
                                  "⚠ The amount is not correct! "
                                  "Only numbers with 2 decimal are allowed\n\n"
                                  f"/{COMMANDS['cancel'].command}")
        return BotState.IMPORT

    async with client.action(user_id, 'typing'):
        logger.info('User Data: %s %s', user_data, amount)
        if user_data['element'] == 'new_expense':
            updated = add_new_expense(user_data['date'], user_data['name'], amount)
        elif user_data['element'] == 'new_earning':
            updated = add_new_earning(user_data['date'], user_data['name'], amount)
        else:
            updated = 0

        if updated > 0:
            await client.send_message(user_id,
                                      f"✅ New element added!\n\n"
                                      f"📆 Date: {user_data['date'].strftime('%d/%m/%Y')}\n"
                                      f"✍ Description: {user_data['name']}\n"
                                      f"💰 Amount: {CURRENCY}{amount}\n")
        else:
            await client.send_message(user_id,
                                      f"⚠ Element not added, retry!")
    conversation_end(update)
    return None


"""
    TABLE, CHART, DELETE ELEMENT START
"""


async def get_chart_date(update, command):
    user_id = get_user_id(update)
    user_data['element'] = command
    date_choose_keyboard = [[Button.inline("👇 This Month", data='this_month'),
                             Button.inline("📅 Calendar", data='calendar')],
                            [Button.inline('✖ Cancel', data='cancel')]]
    await client.send_message(user_id,
                              '⚠ Select the month of the sheet:',
                              buttons=date_choose_keyboard)
    return BotState.NEW_SHEET_CALENDAR if command == 'new_sheet' else BotState.CHART_CALENDAR


"""
    TABLE, CHART, DELETE ELEMENT CHOOSE DATE
"""


async def chart_calendar(update):
    query = update.data.decode('utf-8')
    if query == 'cancel':
        await update.edit('❌ Cancelled')
        conversation_end(update)
        return None

    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if query == 'this_month':
        if min_ <= today.month <= max_:
            return await __get_chart_or_table(update, today)
        else:
            await update.edit(f"⚠ Warning! The month '{today.strftime('%B')}' is not present.\n\n"
                              f"📃 Create a new sheet for the selected month "
                              f"with /{COMMANDS['new_sheet'].command} command")
            conversation_end(update)
            return None

    elif query == 'calendar':
        if min_ != -1 and max_ != -1:
            date_min = date(today.year, min_, 1)
            date_max = date(today.year, max_, calendar.monthrange(today.year, max_)[1])
            user_data['date_min_max'] = date_min, date_max
            cal = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True)
            cal.first_step = 'm'
            cal, step = cal.build()
            await update.edit(f"👉 Select {LSTEP[step]}\n\n"
                              f"/{COMMANDS['cancel'].command}",
                              buttons=cal)
            return BotState.CHART_DATE
        else:
            await update.edit(f"⚠ Warning! No sheets are present.\n\n"
                              f"📃 Create a new one with /{COMMANDS['new_sheet'].command} command")
            conversation_end(update)
            return None


"""
    TABLE, CHART, DELETE ELEMENT CHOOSE FROM CALENDAR
"""


async def set_chart_date(update):
    query = update.data.decode('utf-8')
    date_min, date_max = user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True).process(query)
    if step == 'm' and key:
        await update.edit(f"👉 Select {LSTEP[step]}\n\n"
                          f"/{COMMANDS['cancel'].command}",
                          buttons=key)
        return BotState.NEW_SHEET_DATE if user_data['element'] == 'new_sheet' else BotState.CHART_DATE
    elif step == 'd':
        params = query.split("_")
        params = dict(
            zip(["start", "calendar_id", "action", "step", "year", "month", "day"][:len(params)], params))
        month = int(params["month"])
        today = datetime.today()
        today = date(today.year, month, today.day)
        return await __create_new_sheet(update, today) \
            if user_data['element'] == 'new_sheet' \
            else await __get_chart_or_table(update, today)


# DELETE RESPONSE
async def delete_element(update):
    user_id = get_user_id(update)
    query = update.message.message
    if query == '✖ Cancel':
        await client.send_message(user_id,
                                  '👍 Cancelled.',
                                  buttons=get_keyboard())
    else:
        values = user_data['values']
        try:
            index = values.index(query)
        except ValueError:
            await client.send_message(user_id,
                                      '❗ Element not recognized. '
                                      'Use the keyboard buttons to select the element to remove')
            return BotState.DELETE_ELEMENT

        deleting_mess = await client.send_message(user_id,
                                                  '🔄 Deleting...')
        async with client.action(user_id, 'typing'):
            date_ = user_data['date']

            if user_data['element'] == 'delete_expense':
                delete_expense(date_, index)
            elif user_data['element'] == 'delete_earning':
                delete_earning(date_, index)

            await deleting_mess.delete()
            await client.send_message(user_id,
                                      '👍 Element deleted',
                                      buttons=get_keyboard())
    conversation_end(update)
    return None


# DELETE SECTION
async def __delete_element(update, date_):
    user_id = get_user_id(update)
    await update.edit('🔄 Retrieving data...')
    async with client.action(user_id, 'typing'):
        user_data['date'] = date_
        # delete expense
        if user_data['element'] == 'delete_expense':
            values = get_sheet_expenses(date_)
            if len(values) > 0:
                values = [' '.join(x).strip() for x in values]
                user_data['values'] = values
                keys = build_menu(list(map(lambda x: Button.text(x, resize=True, single_use=True), values)), 1,
                                  header_buttons=Button.text('✖ Cancel'))
                await update.delete()
                await client.send_message(user_id,
                                          '📛 Choose the expense to remove',
                                          buttons=keys)
                return BotState.DELETE_ELEMENT
            else:
                await update.edit(f'⚠ No expense found, add new one with /{COMMANDS["add_expense"].command} command')
                conversation_end(update)
                return None
        # delete earning
        elif user_data['element'] == 'delete_earning':
            values = get_sheet_earnings(date_)
            if len(values) > 0:
                values = [' '.join(x).strip() for x in values]
                user_data['values'] = values
                keys = client.build_reply_markup(
                    build_menu(list(map(lambda x: Button.text(x, resize=True, single_use=True), values)), 1,
                               header_buttons=Button.text('✖ Cancel')))
                await client.send_message(user_id,
                                          '📛 Choose the earning to remove',
                                          buttons=keys)
                return BotState.DELETE_ELEMENT
            else:
                await update.edit(f'⚠ No earning found, add new one with /{COMMANDS["add_earning"].command} command')
        conversation_end(update)
        return None


# SHOW REPORT
async def __show_report(update, date_):
    user_id = get_user_id(update)
    await update.edit('🔄 Retrieving data...')
    async with client.action(user_id, 'typing'):
        surplus, earnings, expenses = get_sheet_report(date_)
        await update.edit(f'💹 Report for {date_.strftime("%B")}\n\n'
                          f'💰  TOTAL EARNINGS: {earnings}\n\n'
                          f'💸  TOTAL EXPENSE: {expenses}\n\n'
                          f'🤑  SURPLUS: {surplus}')
    conversation_end(update)
    return None


# CHART, TABLE SECTION
async def __get_chart_or_table(update, date_):
    chart_date = date_
    user_id = get_user_id(update)
    # get table
    if user_data['element'] == 'show_table':
        await update.edit('🔄 Retrieving the table...')
        async with client.action(user_id, 'photo'):
            image = get_table_from_sheet(chart_date)
            caption = f'Summary Table for {chart_date.strftime("%B")}'
    # get chart
    elif user_data['element'] == 'show_chart':
        await update.edit('🔄 Retrieving the chart...')
        async with client.action(user_id, 'photo'):
            image = get_chart_from_sheet(chart_date, user_id)
            caption = f'Expanses Pie Chart for {chart_date.strftime("%B")}'
    # show report
    elif user_data['element'] == 'show_report':
        return await __show_report(update, date_)
    # delete element
    else:
        return await __delete_element(update, date_)

    if image is None:
        await update.edit('⚠ No data found to create the table')
    else:
        await send_images_helper(user_id, image, caption=caption)
        await update.delete()
    conversation_end(update)
    return None


"""
    NEW SHEET CALENDAR
"""


async def __create_new_sheet(update, date_):
    user_id = get_user_id(update)
    await update.edit('🔄 Creating a new sheet...')
    async with client.action(user_id, 'typing'):
        create_sheet_by_month(date_)
        await update.edit(f'👍 New sheet created for the month {date_.strftime("%B")}')
        conversation_end(update)
        return None


async def new_sheet_date_choose(update):
    query = update.data.decode('utf-8')
    if query == 'cancel':
        await update.edit('❌ Cancelled')
        conversation_end(update)
        return None

    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if query == 'this_month':
        if today.month > max_:
            return await __create_new_sheet(update, today)
        else:
            if max_ < 12:
                await update.edit(f"⚠ Warning! The month '{today.strftime('%B')}' is already present.\n\n"
                                  f"📃 Create a new expense or a new earning "
                                  f"with /{COMMANDS['add_expense'].command} "
                                  f"or /{COMMANDS['add_earning'].command} command")
            else:
                await update.edit(f"⚠ This spreadsheet is full, create a new one in Google Spreadsheet"
                                  f"and set the new SPREADSHEET_ID environment variable\n\n")

    elif query == 'calendar':
        if max_ < 12:
            date_min = date(today.year, max_ + 1, 1)
            date_max = date(today.year, 12, 31)
            user_data['date_min_max'] = date_min, date_max
            cal = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True)
            cal.first_step = 'm'
            cal, step = cal.build()
            await update.edit(f"👉 Select {LSTEP[step]}\n\n"
                              f"/{COMMANDS['cancel'].command}",
                              buttons=cal)
            return BotState.NEW_SHEET_DATE
        else:
            await update.edit(f"⚠ This spreadsheet is full, create a new one in Google Spreadsheet"
                              f"and set the new SPREADSHEET_ID environment variable\n\n")

    conversation_end(update)
    return None


"""
    RECURRENT HANDLERS
"""


async def new_recurrent_type(update, command):
    user_id = get_user_id(update)
    recurrent_choose_keyboard = [[Button.inline("💸 Expense", data='expenses'),
                                  Button.inline("💰 Earning", data='earnings')],
                                 [Button.inline('✖ Cancel', data='cancel')]]
    await client.send_message(user_id,
                              "👉 Select element type\n\n"
                              f"/{COMMANDS['cancel'].command}",
                              buttons=recurrent_choose_keyboard)
    return BotState.SELECT_TYPE if command == 'new_recurrent' else BotState.RECURRENT_DELETE


async def select_recurrent_date(update):
    user_id = get_user_id(update)
    query = update.data.decode('utf-8')
    if query == 'cancel':
        await update.edit('❌ Cancelled')
        conversation_end(update)
        return None

    user_data['type'] = query
    date_min = date(2019, 7, 1)
    date_max = date(2019, 7, 31)
    user_data['date_min_max'] = date_min, date_max
    calendar_ = MyStyleCalendar(max_date=date_max, min_date=date_min, current_date=date_min, telethon=True)
    calendar_.days_of_week = {'en': ["", "", "", "", "", "", ""]}
    calendar_.nav_buttons = {'d': [" ", " ", " "]}
    cal, step = calendar_.build()
    await client.send_message(user_id,
                              "👉 Select the day of the recurrent element\n\n"
                              f"/{COMMANDS['cancel'].command}",
                              buttons=cal)
    return BotState.RECURRENT_DATE


async def new_recurrent_name(update):
    query = update.data.decode('utf-8')
    date_min, date_max = user_data['date_min_max']
    result, key, step = MyStyleCalendar(max_date=date_max, min_date=date_min, telethon=True).process(query)
    if result:
        user_data['day'] = result.day
        await update.edit(f"📆 Date: {result.day} of every month\n\n"
                          f"✍ Insert the description\n\n"
                          f"/{COMMANDS['cancel'].command}")
        return BotState.RECURRENT_NAME


async def new_recurrent_import(update):
    user_id = get_user_id(update)
    user_data['name'] = update.message.message
    await client.send_message(user_id,
                              f"📆 Date: {user_data['day']} of every month\n\n"
                              f"✍ Description: {user_data['name']}\n\n"
                              "💰 Add the amount\n\n"
                              f"/{COMMANDS['cancel'].command}")
    return BotState.RECURRENT_IMPORT


async def new_recurrent_insert(update):
    user_id = get_user_id(update)
    message = update.message.message
    amount = round(fast_float(message, default=-1), 2)
    if amount == -1:
        await client.send_message(user_id,
                                  "⚠ The amount is not correct! "
                                  "Only numbers with 2 decimal are allowed\n\n"
                                  f"/{COMMANDS['cancel'].command}")
        return BotState.RECURRENT_IMPORT

    async with client.action(user_id, 'typing'):
        add_recurrent(user_data['type'], user_data['day'], user_data['name'], amount)
        await client.send_message(user_id,
                                  f"✅ New recurrent element added!\n\n"
                                  f"📆 Date: {user_data['day']} of every month\n"
                                  f"✍ Description: {user_data['name']}\n"
                                  f"💰 Amount: {CURRENCY}{amount}\n")
    conversation_end(update)
    return None


async def select_delete_recurrent(update):
    user_id = get_user_id(update)
    type_ = update.data.decode('utf-8')
    if type_ == 'cancel':
        await update.edit('❌ Cancelled')
        conversation_end(update)
        return None

    user_data['type'] = type_
    await update.edit('🔄 Retrieving data...')
    async with (client.action(user_id, 'typing')):
        values = get_recurrent_elements(type_)
        if len(values) > 0:
            values = list(
                map(lambda val: f'Every {val[0]} of the month  --  {val[1]}  --  {val[3]} {"{:.2f}".format(val[2])}',
                    values))
            user_data['values'] = values
            keys = build_menu(list(map(lambda x: Button.text(x, resize=True, single_use=True), values)), 1,
                              header_buttons=Button.text('✖ Cancel'))
            await client.send_message(user_id,
                                      f'📛 Choose the recurrent {type_[:-1]} to remove',
                                      buttons=keys)
            await update.delete()
            return BotState.RECURRENT_CONFIRM_DELETE
        else:
            await update.edit(
                f'⚠ No recurrent {type_[:-1]} found, add new one with /{COMMANDS["new_recurrent"].command} command')


async def confirm_delete_recurrent(update):
    user_id = get_user_id(update)
    query = update.message.message
    if query == '✖ Cancel':
        await client.send_message(user_id,
                                  '👍 Cancelled.',
                                  buttons=get_keyboard())
    else:
        values = user_data['values']
        try:
            index = values.index(query)
        except ValueError:
            await client.send_message(user_id,
                                      '❗ Element not recognized. '
                                      'Use the keyboard buttons to select the element to remove')
            return BotState.RECURRENT_DELETE

        deleting_mess = await client.send_message(user_id, '🔄 Deleting...')
        async with client.action(user_id, 'typing'):

            elem_type = user_data['type']
            remove_recurrent(elem_type, index)

            await client.send_message(user_id, '👍 Element deleted', buttons=get_keyboard())
            await deleting_mess.delete()
        conversation_end(update)
        return None


"""
    CANCEL COMMAND
"""


async def cancel(update):
    user_id = get_user_id(update)
    await client.send_message(user_id, '❌ Cancelled')


"""
    HELP COMMAND
"""


async def help_command(update):
    user_id = get_user_id(update)
    nl = '\n'
    await client.send_message(user_id,
                              f"⚙️ Commands:\n\n"
                              f"{nl.join(f'• /{key} - {val.description}' for key, val in COMMANDS.items())}"
                              "\n\n\n❓ Have trouble? \n"
                              "• Visit the project page on github\n"
                              "https://github.com/stefanoimperiale/monthly-expenses"
                              )


"""
    ERROR HANDLER FUNCTION
"""


async def error_handler(event, ex):
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    # This is a personal bot, so the user is also the dev
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message
    # could fail

    text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
           "My developer(s) will be notified.<br>"
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.

    # lets put this in a "well" formatted text
    err = '{}: {}'.format(type(ex).__name__, ex)
    text += (f"The error <code>{html.escape(err)}</code> happened{payload}."
             f" The full traceback:\n\n<code>{trace}</code>")

    await client.send_message(USER_ID, text, parse_mode='html', buttons=get_keyboard())
    raise events.StopPropagation
