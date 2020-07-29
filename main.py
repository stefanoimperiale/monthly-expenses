import calendar
import os
import sys
import logging

from telegram.ext import Updater
from bot.handlers import set_handlers

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

MODE = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")

USER_ID = os.getenv("USER_ID")

if MODE is None:
    logger.error("No MODE specified!")
    sys.exit(1)
if TOKEN is None:
    logger.error("No TOKEN specified!")
    sys.exit(1)
if USER_ID is None:
    logger.error("No USER_ID specified!")
    sys.exit(1)

SAMPLE_RANGE_NAME = calendar.month_name[8]


# Getting mode, so we could define run function for local and Heroku setup

if MODE == "dev":
    def run(upd):
        upd.start_polling()

elif MODE == "prod":
    def run(upd):
        port = int(os.environ.get("PORT", "8443"))
        heroku_app_name = os.environ.get("HEROKU_APP_NAME")
        upd.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TOKEN)
        upd.bot.set_webhook(f"https://{heroku_app_name}.herokuapp.com/{TOKEN}")

else:
    logger.error("No MODE specified!")
    sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    set_handlers(dispatcher, USER_ID)
    run(updater)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
