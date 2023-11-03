import logging
import os
import sys
from typing import Type

VERSION = "VERSION 2.0.0"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def get_env(name, default, cast: Type[str | bool | int] = str):
    if name in os.environ:
        return cast(os.environ[name].strip())
    else:
        return default


# Bot env
API_ID = get_env('TG_API_ID', None, int)
API_HASH = get_env('TG_API_HASH', None)
BOT_TOKEN = get_env('TG_BOT_TOKEN', None)
USER_ID = get_env("USER_ID", None, int)
CONFIG_PATH = get_env('CONFIG_PATH', '/config')
CURRENCY = get_env("CURRENCY", '')

# Spreadsheet env
SPREADSHEET_ID = get_env("SPREADSHEET_ID", None)
GOOGLE_APPLICATION_CREDENTIALS_JSON = get_env("GOOGLE_APPLICATION_CREDENTIALS_JSON", None)

TG_SQLITE_FILE = os.path.join(CONFIG_PATH, 'botclient.db')
SESSION = os.path.join(CONFIG_PATH, 'botclient')

if API_ID is None or API_HASH is None or BOT_TOKEN is None:
    logger.error("No TOKEN specified!")
    sys.exit(1)
if SPREADSHEET_ID is None:
    logger.error("No SPREADSHEET_ID specified!")
    sys.exit(1)
if USER_ID is None:
    logger.error("No USER_ID specified!")
    sys.exit(1)
if GOOGLE_APPLICATION_CREDENTIALS_JSON is None:
    logger.error("No GOOGLE_APPLICATION_CREDENTIALS_JSON specified!")
    sys.exit(1)
if CURRENCY == '':
    logger.info("No currency specified, EUR set by default")
    CURRENCY = '€'
