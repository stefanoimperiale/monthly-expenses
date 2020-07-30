import asyncio
import io
import logging
import os
import sys
import threading
from datetime import datetime
from decimal import Decimal
from re import sub

import imgkit
from telegram_bot_calendar import DetailedTelegramCalendar

from html_render.requests_html import HTML
from sheet.sheet_service import SheetService

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SPREADSHEET_ID = os.getenv("SHEET_ID")
CURRENCY = os.getenv("CURRENCY")
if SPREADSHEET_ID is None:
    logger.error("No SHEET_ID specified!")
    sys.exit(1)
if CURRENCY is None:
    logger.info("No currency specified, EUR setted by default")
    CURRENCY = '€'

page_template = """
        <html>
          <head>
          <meta charset="utf-8">
            <title>Monthly Example</title>
            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            <script type="text/javascript">
              google.charts.load('current', {'packages':['corechart']});
              google.setOnLoadCallback(drawTable);
              function drawTable() {
                var json_data = new google.visualization.arrayToDataTable(%(json)s);
                var formatter = new google.visualization.NumberFormat({prefix: '""" + CURRENCY + """ '});
                formatter.format(json_data, 1)
                var options = {
                    title: 'Monthly expenses',
                    is3D: true,
                    pieSliceText: 'label',
                    sliceVisibilityThreshold: 0,
                    legend: {
                        labeledValueText: 'both',
                        position: 'labeled'
                    }
                };
                var chart = new google.visualization.PieChart(document.getElementById('piechart_3d'))
                chart.draw(json_data, options);
              }
            </script>
          </head>
          <body>
            <div id="piechart_3d" style="width: 900px; height: 500px;"></div>
          </body>
        </html>
        """


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


def add_new_sheet_element(date: datetime.date, name: str, amount: float, start_range: str):
    month = date.strftime("%B")
    values = [
        [date.strftime('%d/%m/%Y'), name, amount]
    ]
    updated = SheetService().write_sheet(SPREADSHEET_ID, f'{month}!{start_range}', values)
    return updated


def add_new_expense(date: datetime.date, name: str, amount: float):
    return add_new_sheet_element(date, name, amount, 'E3')


def add_new_gain(date: datetime.date, name: str, amount: float):
    return add_new_sheet_element(date, name, amount, 'A3')


def convert_to_decimal(value):
    conversion = list()
    conversion.insert(0, value[0])
    amount = value[1]
    if CURRENCY == '€':
        amount = amount.replace(',', '.')
    conversion.insert(1, float(Decimal(sub(r'[^\d.]', '', amount))))
    return conversion


def render(html_, loop):
    asyncio.set_event_loop(loop)
    html_.render(reload=False)


def get_chart_from_sheet(date):
    month = date.strftime("%B")
    result = SheetService().read_sheet(SPREADSHEET_ID, f'{month}!F2:G')
    values = result.get('values', [])
    title = values[0]
    values = list(map(convert_to_decimal, values[1:]))
    values.insert(0, title)
    html = HTML(html=str(page_template % {"json": values}))
    loop = asyncio.new_event_loop()
    text = threading.Thread(target=render, args=(html, loop))
    text.start()
    text.join()
    # UBUNTU config = imgkit.config(wkhtmltoimage='.apt/usr/local/bin/wkhtmltoimage')
    config = imgkit.config(wkhtmltoimage='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe')
    img = imgkit.from_string(html.find('#piechart_3d')[0].html, False, config=config, options={
        'format': 'png',
        'crop-w': '650',
        'crop-x': '150',
        'crop-y': '50',
        'crop-h': '400',
        'encoding': 'utf-8',
    })
    str_file = io.BytesIO(img)
    return str_file


class MyStyleCalendar(DetailedTelegramCalendar):
    # previous and next buttons style. they are emoji now!
    prev_button = "⬅️"
    next_button = "➡️"
    # you do not want empty cells when month and year are being selected
    empty_month_button = ""
    empty_year_button = ""
    first_step = "d"
    middle_button_year = ''
