import datetime

from app.bot.bot_utils import add_new_expense, add_new_earning
from app.wise.wise_api_request import get_profiles, get_borderless_accounts, get_transactions


async def retrieve_wise_transactions():
    transactions = []
    profile_ids = get_profiles()
    for profile_id in profile_ids:
        account_ids = get_borderless_accounts(profile_id)
        for account_id in account_ids:
            trans = get_transactions(profile_id, account_id)
            transactions.extend(trans)
    for transaction in transactions:
        type = transaction['type']
        date = transaction['date']
        date = datetime.datetime.fromisoformat(date).astimezone()
        amount = transaction['amount']['value']
        currency = transaction['amount']['currency']
        description = transaction['details']['description']
        if type == 'DEBIT':
            amount = -amount
            add_new_expense(date, description, amount)
        else:
            add_new_earning(date, description, amount)
