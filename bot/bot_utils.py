import asyncio
import calendar
import io
import json
import logging
import os
import threading
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError
from re import sub
from time import strptime

import imgkit
import plotly.graph_objects as go
from kaleido.scopes.plotly import PlotlyScope
from telegram_bot_calendar import DetailedTelegramCalendar

from bot.html_template import chart_template
from bot.spreadsheet_format import get_sheet_format, table_titles
from env_variables import SPREADSHEET_ID, CURRENCY
from html_render.requests_html import HTML, HTMLSession
from sheet.sheet_service import SheetService

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

recurrent_file = os.path.join(os.path.dirname(__file__), 'recurrent.json')


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
    updated = SheetService().write_append_sheet(SPREADSHEET_ID, f'{month}!{start_range}', values)
    return updated


def add_new_expense(date: datetime.date, name: str, amount: float):
    return add_new_sheet_element(date, name, amount, 'E3')


def add_new_earning(date: datetime.date, name: str, amount: float):
    return add_new_sheet_element(date, name, amount, 'A3')


def convert_to_decimal(value):
    conversion = list()
    conversion.insert(0, value[0])
    amount = value[1]
    if CURRENCY == '€':
        amount = amount.replace('.', '').replace(',', '.')
    conversion.insert(1, float(Decimal(sub(r'[^\d.]', '', amount))))
    return conversion


def render(html_, loop):
    asyncio.set_event_loop(loop)
    html_.render(reload=False)


def __get_data_from_sheet(data, template, imgkit_options, selector=None):
    html = HTML(session=HTMLSession(browser_args=['--start-maximized', '--no-sandbox']),
                html=str(template % {"json": data}))
    loop = asyncio.new_event_loop()
    text = threading.Thread(target=render, args=(html, loop))
    text.start()
    text.join()
    # HEROKU
    # config = imgkit.config(wkhtmltoimage='.apt/usr/local/bin/wkhtmltoimage')
    config = imgkit.config(wkhtmltoimage='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe')
    content = html.html
    if selector is not None:
        content = html.find(selector)[0].html
    img = imgkit.from_string(content, False, config=config, options=imgkit_options)
    str_file = io.BytesIO(img)
    return str_file


def get_table_from_sheet(date):
    month = date.strftime("%B")
    result = SheetService().read_sheet_multiple(SPREADSHEET_ID,
                                                [f'{month}!A2:C', f'{month}!E2:G', f'{month}!I2:K'],
                                                major_dimension='COLUMNS')
    values = result.get('valueRanges', [])
    header = []
    l_ = []
    if len(values) > 0:
        for val in values:
            header = header + [item[0] for item in val['values']]
            l_ = l_ + [i[1:] for i in val['values']]
        scope = PlotlyScope()
        fig = go.Figure(data=[go.Table(
            columnwidth=[80, 150, 100, 80, 150, 100, 100, 100],
            header=dict(values=header),
            cells=dict(values=l_,
                       fill=dict(
                           color=['lightgreen', 'lightgreen', 'lightgreen', '#ff9982', '#ff9982', '#ff9982',
                                  '#ffbf70', '#ffbf70']),
                       height=30
                       )
        )
        ])
        test = scope.transform(fig, format="png", scale=2)
        str_file = io.BytesIO(test)
        return str_file
    else:
        return None


def get_chart_from_sheet(date):
    month = date.strftime("%B")
    result = SheetService().read_sheet(SPREADSHEET_ID, f'{month}!F2:G')
    values = result.get('values', [])
    if len(values) == 0:
        return None

    title = values[0]
    values = list(map(convert_to_decimal, values[1:]))
    values.insert(0, title)
    html = HTML(html=str(chart_template % {"json": values}))
    loop = asyncio.new_event_loop()
    text = threading.Thread(target=render, args=(html, loop))
    text.start()
    text.join()
    # HEROKU PATH
    # config = imgkit.config(wkhtmltoimage='.apt/usr/local/bin/wkhtmltoimage')
    config = imgkit.config(wkhtmltoimage='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe')
    content = html.find('#content')[0].html
    img = imgkit.from_string(content, False, config=config, options={
        'format': 'png',
        'crop-w': '650',
        'crop-x': '150',
        'crop-y': '50',
        'crop-h': '400',
        'encoding': 'utf-8',
    })
    str_file = io.BytesIO(img)
    return str_file


def get_sheet_min_max_month():
    spreadsheet = SheetService().get_spreadsheet(SPREADSHEET_ID, [], False)
    sheets = spreadsheet['sheets']
    if len(sheets) > 0:
        first = sheets[0]
        last = sheets[-1]
        try:
          first_month = strptime(first['properties']['title'], '%B').tm_mon
          last_month = strptime(last['properties']['title'], '%B').tm_mon
        except ValueError as e:
          print ('error type: ', type (e))
          return -1, -1

        logger.info('first month %s, last month %s', first_month, last_month)
        return first_month, last_month
    else:
        return -1, -1


def get_sheet_expenses(date, value_render_option='FORMATTED_VALUE'):
    month = date.strftime("%B")
    result = SheetService().read_sheet(SPREADSHEET_ID, f'{month}!E3:G', value_render_option=value_render_option)
    values = result.get('values', [])
    return values


def get_sheet_earnings(date, value_render_option='FORMATTED_VALUE'):
    month = date.strftime("%B")
    result = SheetService().read_sheet(SPREADSHEET_ID, f'{month}!A3:C', value_render_option=value_render_option)
    values = result.get('values', [])
    return values


def delete_expense(date, index):
    month = date.strftime("%B")
    values = get_sheet_expenses(date, 'UNFORMATTED_VALUE')
    del values[index]
    values.append(["", "", ""])
    SheetService().write_sheet(SPREADSHEET_ID, f'{month}!E3:G', values)


def delete_earning(date, index):
    month = date.strftime("%B")
    values = get_sheet_earnings(date, 'UNFORMATTED_VALUE')
    del values[index]
    values.append(["", "", ""])
    SheetService().write_sheet(SPREADSHEET_ID, f'{month}!A3:C', values)


def get_sheet_report(date):
    month = date.strftime("%B")
    result = SheetService().read_sheet(SPREADSHEET_ID, f'{month}!I3:K3')
    values = result.get('values', [])
    return values[0][0], values[0][1], values[0][2]


def __get_serial_number_from_date(date):
    temp = datetime(1899, 12, 30)
    delta = date - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


def __get_values_for_update(values, date_):
    return list(map(lambda val: {"values": [
        {"userEnteredValue": {"numberValue": __get_serial_number_from_date(
            datetime(date_.year, date_.month, min(val[0], calendar.monthrange(date_.year, date_.month)[1])))},
            "userEnteredFormat": {
                "numberFormat": {
                    "type": "DATE",
                    "pattern": "dd-mmm"
                },
                "horizontalAlignment": 'CENTER',
                "verticalAlignment": 'MIDDLE',
            }},
        {"userEnteredValue": {"stringValue": val[1]}, "userEnteredFormat": {
            "horizontalAlignment": 'CENTER',
            "verticalAlignment": 'MIDDLE',
        }},
        {"userEnteredValue": {"numberValue": val[2]}, "userEnteredFormat": {
            "numberFormat": {
                "type": "CURRENCY"
            },
            "horizontalAlignment": 'CENTER',
            "verticalAlignment": 'MIDDLE',
        }}
    ]}, values))


def create_sheet_by_month(date):
    sheet_service = SheetService()

    sheet_properties = sheet_service.add_sheet(SPREADSHEET_ID, date.strftime("%B"))
    sheet_id = sheet_properties['sheetId']
    requests = get_sheet_format(sheet_id)
    requests = requests + [
        {
            "updateCells": {
                "rows": [
                    {
                        "values": table_titles
                    }
                ],
                "fields": "*",
                "start": {
                    "sheetId": sheet_id,
                    "rowIndex": 1,
                    "columnIndex": 0
                }
            }
        }
    ]

    # Check recurrent elements
    with open(recurrent_file, 'a+') as json_file:
        try:
            data = json.load(json_file)
            if len(data['earnings']) > 0:
                requests = requests + [
                    {
                        "updateCells": {
                            "rows": __get_values_for_update(data['earnings'], date),
                            "fields": "*",
                            "start": {
                                "sheetId": sheet_id,
                                "rowIndex": 2,
                                "columnIndex": 0
                            }
                        }
                    }
                ]
            if len(data['expenses']) > 0:
                requests = requests + [
                    {
                        "updateCells": {
                            "rows": __get_values_for_update(data['expenses'], date),
                            "fields": "*",
                            "start": {
                                "sheetId": sheet_id,
                                "rowIndex": 2,
                                "columnIndex": 4
                            }
                        }
                    }
                ]
        except JSONDecodeError:
            pass

    sheet_service.update_sheet(SPREADSHEET_ID, requests)


def add_recurrent(elem_type, day, name, amount):
    with open(recurrent_file, 'a+') as infile:
        infile.seek(0)
        try:
            data = json.load(infile)
        except JSONDecodeError:
            data = {
                "earnings": [],
                "expenses": []
            }
    with open(recurrent_file, 'w') as outfile:
        data[elem_type].append([day, name, amount])
        json.dump(data, outfile)


def get_recurrent_elements(elem_type):
    with open(recurrent_file, 'a+') as infile:
        infile.seek(0)
        try:
            data = json.load(infile)
            return data[elem_type]
        except JSONDecodeError:
            return []


def remove_recurrent(elem_type, index):
    with open(recurrent_file, 'r') as infile:
        data = json.load(infile)
    with open(recurrent_file, 'w') as outfile:
        del data[elem_type][index]
        json.dump(data, outfile)


class MyStyleCalendar(DetailedTelegramCalendar):
    # previous and next buttons style. they are emoji now!
    prev_button = "⬅️"
    next_button = "➡️"
    # you do not want empty cells when month and year are being selected
    empty_month_button = "❌"
    empty_year_button = "❌"
    first_step = "d"
