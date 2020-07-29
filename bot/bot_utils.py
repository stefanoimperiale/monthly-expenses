import logging
import os
import sys
from datetime import datetime

from telegram_bot_calendar import DetailedTelegramCalendar

from sheet.sheet_service import SheetService

SPREADSHEET_ID = os.getenv("SHEET_ID")
if SPREADSHEET_ID is None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error("No SHEET_ID specified!")
    sys.exit(1)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """Helper for build menu or keyboard buttons"""
    menu = list_in_chunks(buttons, n_cols)
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def list_in_chunks(orig_list, chunk_dim):
    """Divide a list in a list of lists of at least 'chunk_dim' size """
    return [orig_list[i:i + chunk_dim] for i in range(0, len(orig_list), chunk_dim)]


def add_new_sheet_element(date: datetime.date, name: str, amount: float):
    month = date.strftime("%B")
    values = [
       [date.strftime('%d/%m/%Y'), amount, name]
    ]
    updated = SheetService().write_sheet(SPREADSHEET_ID, f'{month}!E3', values)
    return updated


class MyStyleCalendar(DetailedTelegramCalendar):
    # previous and next buttons style. they are emoji now!
    prev_button = "⬅️"
    next_button = "➡️"
    # you do not want empty cells when month and year are being selected
    empty_month_button = ""
    empty_year_button = ""
