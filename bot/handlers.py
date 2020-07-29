from telegram.ext import \
    CommandHandler, Dispatcher, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from bot.commands import unknown, error, start, keyboard, DATE, new_element, NAME, add_name, cancel, calendar, \
    SET_CALENDAR, choose_date, IMPORT, add_import


def set_handlers(dispatcher: Dispatcher, user_id):
    start_handler = CommandHandler('start', start, Filters.user(user_id=int(user_id)))
    dispatcher.add_handler(start_handler)

    new_el_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text(keyboard[:2]), new_element)],
        states={
            SET_CALENDAR: [CallbackQueryHandler(calendar)],
            DATE: [CallbackQueryHandler(choose_date)],
            NAME: [MessageHandler((~ Filters.command & ~ Filters.text(keyboard)) & Filters.text, add_name)],
            IMPORT: [MessageHandler((~ Filters.command & ~ Filters.text(keyboard)) & Filters.text, add_import)]
        },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.text(keyboard), new_element)],
    )
    dispatcher.add_handler(new_el_handler)

    #
    # caps_handler = CommandHandler('set_month', set_month)
    # dispatcher.add_handler(caps_handler)
    #
    # caps_handler = CommandHandler('new_expanse', new_expanse)
    # dispatcher.add_handler(caps_handler)
    #
    # caps_handler = CommandHandler('new_gain', new_gain)
    # dispatcher.add_handler(caps_handler)
    #
    # caps_handler = CommandHandler('show_report', new_gain)
    # dispatcher.add_handler(caps_handler)
    #
    # inline_caps_handler = InlineQueryHandler(inline_query)
    # dispatcher.add_handler(inline_caps_handler)

    # log all errors
    dispatcher.add_error_handler(error)

    # unknown message handler, must be the last
    unknown_handler = MessageHandler(Filters.all, unknown)
    dispatcher.add_handler(unknown_handler)
