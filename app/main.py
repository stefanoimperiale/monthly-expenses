import asyncio
import functools
import threading

from telethon import events, functions, types, TelegramClient

from app.bot.bot_utils import get_user_id
from app.bot.commands import unknown, start, keyboard, new_element, cancel, not_allowed, COMMANDS, help_command, \
    get_chart_date, new_recurrent_type
from app.bot.handlers import handle_callback, handle_message_callback
from app.client import client, get_state, conversation_end, set_state
from app.env_variables import USER_ID, logger, VERSION
from app.webserver.server import appFlask
from bot.commands import error_handler
from env_variables import BOT_TOKEN

# THIS PATCHES THE add_event_handler METHOD
orig_add_event_handler = TelegramClient.add_event_handler


@functools.wraps(TelegramClient.add_event_handler)
def patched_add_event_handler(cl, callback, event_builder=None):
    @functools.wraps(callback)
    async def new_callback(event):
        try:
            return await callback(event)
        except events.StopPropagation as ev:
            raise ev
        except Exception as e:
            logger.exception("Error occurred while handling an event")
            conversation_end(event)
            return await error_handler(event, e)

    orig_add_event_handler(cl, new_callback, event_builder)


TelegramClient.add_event_handler = patched_add_event_handler


@client.on(events.CallbackQuery())
async def callback_query_handler(event):
    await event.answer()
    state = get_state(event)
    s = await handle_callback(event, state)
    if s is not None:
        set_state(event, s)
    raise events.StopPropagation


@client.on(events.NewMessage(incoming=True))
async def check_user(event):
    user_id = get_user_id(event)
    if USER_ID != user_id:
        await not_allowed(event)
        raise events.StopPropagation


@client.on(events.NewMessage(pattern='/cancel', from_users=USER_ID))
async def cancel_callback(event):
    await cancel(event)
    conversation_end(event)
    raise events.StopPropagation


@client.on(events.NewMessage(pattern="/start", from_users=USER_ID))
async def start_callback(event):
    await start(event)
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr"/help|{keyboard['help'].button.text}", from_users=USER_ID))
async def help_callback(event):
    await help_command(event)
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr"{keyboard['new_expense'].button.text}|{keyboard['new_earning'].button.text}",
                             from_users=USER_ID))
async def add_expense_callback(event):
    set_state(event, await new_element(event, 'new_expense' if event.message.message == keyboard[
        'new_expense'].button.text else 'new_earning'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern='/add_expense', from_users=USER_ID))
async def add_expense_callback(event):
    set_state(event, await new_element(event, 'new_expense'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern='/add_earning', from_users=USER_ID))
async def add_earning_callback(event):
    set_state(event, await new_element(event, 'new_earning'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/show_table|{keyboard["show_table"].button.text}', from_users=USER_ID))
async def show_table_callback(event):
    set_state(event, await get_chart_date(event, 'show_table'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/show_chart|{keyboard["show_graph"].button.text}', from_users=USER_ID))
async def show_chart_callback(event):
    set_state(event, await get_chart_date(event, 'show_chart'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/delete_expense|{keyboard["delete_expense"].button.text}', from_users=USER_ID))
async def delete_expense_callback(event):
    set_state(event, await get_chart_date(event, 'delete_expense'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/delete_earning|{keyboard["delete_earning"].button.text}', from_users=USER_ID))
async def delete_earning_callback(event):
    set_state(event, await get_chart_date(event, 'delete_earning'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/show_report|{keyboard["show_report"].button.text}', from_users=USER_ID))
async def show_report_callback(event):
    set_state(event, await get_chart_date(event, 'show_report'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/new_sheet|{keyboard["new_sheet"].button.text}', from_users=USER_ID))
async def new_sheet_callback(event):
    set_state(event, await get_chart_date(event, 'new_sheet'))
    raise events.StopPropagation


@client.on(events.NewMessage(pattern=fr'/new_recurrent|{keyboard["new_recurrent"].button.text}', from_users=USER_ID))
async def new_recurrent_callback(event):
    set_state(event, await new_recurrent_type(event, 'new_recurrent'))
    raise events.StopPropagation


@client.on(
    events.NewMessage(pattern=fr'/delete_recurrent|{keyboard["delete_recurrent"].button.text}', from_users=USER_ID))
async def delete_recurrent_callback(event):
    set_state(event, await new_recurrent_type(event, 'delete_recurrent'))
    raise events.StopPropagation


@client.on(events.NewMessage(from_users=int(USER_ID)))
async def handle_states(event):
    state = get_state(event)
    if state is None:
        return
    s = await handle_message_callback(event, state)
    if s is not None:
        set_state(event, s)
    raise events.StopPropagation


@client.on(events.NewMessage(from_users=USER_ID))
async def unknown_callback(event):
    await unknown(event)
    raise events.StopPropagation


client.start(bot_token=BOT_TOKEN)

if __name__ == '__main__':
    from waitress import serve

    loop = asyncio.get_event_loop()
    try:
        threading.Thread(target=lambda: serve(appFlask, host="0.0.0.0", port=5500)).start()
        client.add_event_handler(check_user)
        loop.run_until_complete(client(functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code='en',
            commands=COMMANDS.values()
        )))
        logger.info("%s" % VERSION)
        logger.info("********** START MONTHLY expenseS **********")
        client.run_until_disconnected()
    finally:
        client.disconnect()
        logger.info("********** STOPPED **********")
