import logging
import os
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot env
MODE = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")
# Heroku env
HEROKU_APP = os.getenv("HEROKU_APP_NAME")
HEROKU_PORT = os.getenv("PORT", "8443")

# Spreadsheet env
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
CURRENCY = os.getenv("CURRENCY")

if MODE is None:
    logger.error("No MODE specified!")
    sys.exit(1)
if TOKEN is None:
    logger.error("No TOKEN specified!")
    sys.exit(1)
if SPREADSHEET_ID is None:
    logger.error("No SHEET_ID specified!")
    sys.exit(1)
if USER_ID is None:
    logger.error("No USER_ID specified!")
    sys.exit(1)
if CURRENCY is None:
    logger.info("No currency specified, EUR setted by default")
    CURRENCY = '€'
