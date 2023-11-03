from app.bot.commands import choose_date, calendar_set, add_name, add_import, chart_calendar, set_chart_date, \
    delete_element, new_sheet_date_choose, new_recurrent_import, new_recurrent_insert, select_recurrent_date, \
    new_recurrent_name, select_delete_recurrent, confirm_delete_recurrent
from app.client import BotState


async def handle_callback(event, state):
    if state is not None:
        match state:
            case BotState.DATE:
                return await choose_date(event)
            case BotState.SET_CALENDAR:
                return await calendar_set(event)
            case BotState.CHART_CALENDAR:
                return await chart_calendar(event)
            case BotState.CHART_DATE:
                return await set_chart_date(event)
            case BotState.NEW_SHEET_CALENDAR:
                return await new_sheet_date_choose(event)
            case BotState.NEW_SHEET_DATE:
                return await set_chart_date(event)
            case BotState.SELECT_TYPE:
                return await select_recurrent_date(event)
            case BotState.RECURRENT_DATE:
                return await new_recurrent_name(event)
            case BotState.RECURRENT_DELETE:
                return await select_delete_recurrent(event)


async def handle_message_callback(event, state):
    match state:
        case BotState.NAME:
            return await add_name(event)
        case BotState.IMPORT:
            return await add_import(event)
        case BotState.DELETE_ELEMENT:
            return await delete_element(event)
        case BotState.RECURRENT_NAME:
            return await new_recurrent_import(event)
        case BotState.RECURRENT_IMPORT:
            return await new_recurrent_insert(event)
        case BotState.RECURRENT_CONFIRM_DELETE:
            return await confirm_delete_recurrent(event)
