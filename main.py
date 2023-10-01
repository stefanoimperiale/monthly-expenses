import calendar
import os
import sys
import logging

from telegram.ext import Updater
from bot.handlers import set_handlers
from env_variables import MODE, TOKEN, SERVER_URL, SERVER_PORT

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Getting mode, so we could define run function for local and Heroku setup
if MODE == "dev":
    def run(upd):
        upd.start_polling()

elif MODE == "prod":
    def run(upd):
        if SERVER_URL == "" or SERVER_URL is None:
            logger.error("No SERVER_URL specified!")
            sys.exit(1)
        port = int(SERVER_PORT)
        upd.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TOKEN,
                          webhook_url=f"https://{SERVER_URL}/{TOKEN}")

else:
    logger.error("No MODE specified!")
    sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    set_handlers(dispatcher)
    run(updater)

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
