from telegram.ext import \
    CommandHandler, Dispatcher, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from bot.commands import unknown, error, start, keyboard, DATE, new_element, NAME, add_name, cancel, calendar, \
    SET_CALENDAR, choose_date, IMPORT, add_import, CHART_CALENDAR, CHART_DATE, get_chart_date, \
    chart_calendar, set_chart_date

text_filter = (~ Filters.command & ~ Filters.text(keyboard)) & Filters.text


def set_handlers(dispatcher: Dispatcher, user_id):
    def message_filter(keyboard_):
        return Filters.user(user_id=int(user_id)) & Filters.text(keyboard_)

    start_handler = CommandHandler('start', start, Filters.user(user_id=int(user_id)))
    dispatcher.add_handler(start_handler)

    new_el_handler = ConversationHandler(
        entry_points=[MessageHandler(message_filter(keyboard[:2]), new_element)],
        states={
            SET_CALENDAR: [CallbackQueryHandler(calendar)],
            DATE: [CallbackQueryHandler(choose_date)],
            NAME: [MessageHandler(text_filter, add_name)],
            IMPORT: [MessageHandler(text_filter, add_import)]
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   MessageHandler(message_filter(keyboard[:2]), new_element)],
    )
    dispatcher.add_handler(new_el_handler)

    chart_handler = ConversationHandler(
        entry_points=[MessageHandler(message_filter(keyboard[3]), get_chart_date)],
        states={
            CHART_CALENDAR: [CallbackQueryHandler(chart_calendar)],
            CHART_DATE: [CallbackQueryHandler(set_chart_date)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(message_filter(keyboard[3]), get_chart_date)
        ]
    )
    dispatcher.add_handler(chart_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # unknown message handler, must be the last
    unknown_handler = MessageHandler(Filters.all, unknown)
    dispatcher.add_handler(unknown_handler)
