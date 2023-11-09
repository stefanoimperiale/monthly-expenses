import re
from datetime import date

import dateutil.parser

from app.bot.bot_utils import add_new_expense, add_new_earning, get_sheet_min_max_month, create_sheet_by_month
from app.wise.wise_api_request import get_profiles, get_borderless_accounts, get_transactions


async def retrieve_wise_transactions():
    transactions = []
    min_, max_ = get_sheet_min_max_month()
    today = date.today()
    if today.month > max_ or today.month < min_:
        create_sheet_by_month(today)
    profile_ids = get_profiles()
    for profile_id in profile_ids:
        account_ids = get_borderless_accounts(profile_id)
        for account_id in account_ids:
            trans = get_transactions(profile_id, account_id)
            transactions.extend(trans)
    for transaction in transactions:
        type_val = transaction['type']
        date_val = transaction['date']
        date_val = dateutil.parser.isoparse(date_val).astimezone()
        amount = transaction['amount']['value']
        currency = transaction['amount']['currency']
        description = transaction['details']['description']
        re.sub(r'Card transaction of (.*) issued by ', '', description)

        if type_val == 'DEBIT':
            amount = -amount
            add_new_expense(date_val, description, amount, currency)
        else:
            add_new_earning(date_val, description, amount, currency)
