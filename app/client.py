from enum import Enum, auto

from telethon import TelegramClient

from app.bot.bot_utils import get_user_id
from env_variables import SESSION, API_ID, API_HASH


class BotState(Enum):
    DATE = auto()
    SET_CALENDAR = auto()
    NAME = auto()
    IMPORT = auto()
    CHART_CALENDAR = auto()
    CHART_DATE = auto()
    DELETE_ELEMENT = auto()
    NEW_SHEET_CALENDAR = auto()
    NEW_SHEET_DATE = auto()
    SELECT_TYPE = auto()
    RECURRENT_DATE = auto()
    RECURRENT_NAME = auto()
    RECURRENT_IMPORT = auto()
    RECURRENT_DELETE = auto()
    RECURRENT_CONFIRM_DELETE = auto()


session = SESSION
client = TelegramClient(session, API_ID, API_HASH)
user_data = dict()

# The state in which different users are, {user_id: state}
conversation_state = {}


def set_state(event, state):
    who = get_user_id(event)
    conversation_state[who] = state


def get_state(event):
    who = get_user_id(event)
    return conversation_state.get(who)


def conversation_end(event):
    who = get_user_id(event)
    if who in conversation_state:
        del conversation_state[who]
    user_data.clear()
