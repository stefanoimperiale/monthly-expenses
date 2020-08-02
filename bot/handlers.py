from telegram.ext import \
    CommandHandler, Dispatcher, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from bot.commands import unknown, error, start, keyboard, DATE, new_element, NAME, add_name, cancel, calendar_set, \
    SET_CALENDAR, choose_date, IMPORT, add_import, CHART_CALENDAR, CHART_DATE, get_chart_date, \
    chart_calendar, set_chart_date, not_allowed, DELETE_ELEMENT, delete_element, COMMANDS, NEW_SHEET_CALENDAR, \
    NEW_SHEET_DATE, ADD_SHEET, new_sheet_date_choose
from env_variables import USER_ID

text_filter = (~ Filters.command & ~ Filters.text(keyboard)) & Filters.text


def set_handlers(dispatcher: Dispatcher):
    def message_filter(keyboard_):
        return Filters.user(user_id=int(USER_ID)) & Filters.text(keyboard_)

    dispatcher.bot.set_my_commands(COMMANDS.values())

    start_handler = CommandHandler(COMMANDS['start'].command, start, Filters.user(user_id=int(USER_ID)))
    dispatcher.add_handler(start_handler)

    new_element_entry_points = [
        MessageHandler(message_filter(keyboard[:2]), new_element),
        CommandHandler(COMMANDS['add_expense'].command,
                       lambda update, context: new_element(update, context, keyboard[0]),
                       Filters.user(user_id=int(USER_ID))),
        CommandHandler(COMMANDS['add_gain'].command,
                       lambda update, context: new_element(update, context, keyboard[1]),
                       Filters.user(user_id=int(USER_ID)))
    ]

    new_el_handler = ConversationHandler(
        entry_points=new_element_entry_points,
        states={
            SET_CALENDAR: [CallbackQueryHandler(calendar_set)],
            DATE: [CallbackQueryHandler(choose_date)],
            NAME: [MessageHandler(text_filter, add_name)],
            IMPORT: [MessageHandler(text_filter, add_import)]
        },
        fallbacks=[CommandHandler(COMMANDS['cancel'].command, cancel)] + new_element_entry_points,
    )
    dispatcher.add_handler(new_el_handler)

    select_month_entry_points = [
        MessageHandler(message_filter(keyboard[2:7]), get_chart_date),
        CommandHandler(COMMANDS['show_table'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[2]),
                       Filters.user(user_id=int(USER_ID))),
        CommandHandler(COMMANDS['show_chart'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[3]),
                       Filters.user(user_id=int(USER_ID))),
        CommandHandler(COMMANDS['delete_expense'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[4]),
                       Filters.user(user_id=int(USER_ID))),
        CommandHandler(COMMANDS['delete_gain'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[5]),
                       Filters.user(user_id=int(USER_ID))),
        CommandHandler(COMMANDS['show_report'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[6]),
                       Filters.user(user_id=int(USER_ID)))
    ]
    new_sheet_entry_point = [
        MessageHandler(message_filter(keyboard[7]), get_chart_date),
        CommandHandler(COMMANDS['new_sheet'].command,
                       lambda update, context: get_chart_date(update, context, keyboard[7]),
                       Filters.user(user_id=int(USER_ID))),
    ]

    chart_handler = ConversationHandler(
        entry_points=select_month_entry_points,
        states={
            CHART_CALENDAR: [CallbackQueryHandler(chart_calendar)],
            CHART_DATE: [CallbackQueryHandler(set_chart_date)],
            DELETE_ELEMENT: [MessageHandler(text_filter, delete_element)]
        },
        fallbacks=[CommandHandler(COMMANDS['cancel'].command,
                                  cancel)] + select_month_entry_points + new_sheet_entry_point
    )
    dispatcher.add_handler(chart_handler)

    new_sheet_handler = ConversationHandler(
        entry_points=new_sheet_entry_point,
        states={
            NEW_SHEET_CALENDAR: [CallbackQueryHandler(new_sheet_date_choose)],
            NEW_SHEET_DATE: [CallbackQueryHandler(set_chart_date)]
        },
        fallbacks=[CommandHandler(COMMANDS['cancel'].command,
                                  cancel)] + select_month_entry_points + new_sheet_entry_point
    )
    dispatcher.add_handler(new_sheet_handler)

    # User not  allowed
    user_not_allowed_handler = MessageHandler(~Filters.user(user_id=int(USER_ID)), not_allowed)
    dispatcher.add_handler(user_not_allowed_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # unknown message handler, must be the last
    unknown_handler = MessageHandler(Filters.all, unknown)
    dispatcher.add_handler(unknown_handler)
