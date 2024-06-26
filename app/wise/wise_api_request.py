import base64
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import rsa
import urllib3

from app.env_variables import logger, CURRENCY, WISE_API_TOKEN, WISE_PRIVATE_KEY

private_key_path = WISE_PRIVATE_KEY  # Change to private key path
base_url = 'https://api.transferwise.com'

token = WISE_API_TOKEN
http = urllib3.PoolManager()


def get_profiles():
    url = base_url + '/v2/profiles'
    profiles = get_statement(url)
    profile_ids = list(map(lambda x: x['id'], profiles))
    return profile_ids


def get_borderless_accounts(profile_id):
    url = base_url + f'/v1/borderless-accounts?profileId={profile_id}'
    accounts = get_statement(url)
    account_ids = list(map(lambda x: x['id'], accounts))
    return account_ids


def get_transactions(profile_id, account_id):
    interval_start = ((datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                      .astimezone(timezone.utc).isoformat())
    interval_end = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
                    .isoformat())
    # 1 day
    params = urlencode({
        'currency': CURRENCY,
        'type': 'COMPACT',
        'intervalStart': interval_start,
        'intervalEnd': interval_end
    })

    url = (base_url + f'/v3/profiles/{profile_id}/borderless-accounts/{account_id}/statement.json?' + params)
    statement = get_statement(url)

    if 'transactions' in statement:
        return statement['transactions']
    else:
        logger.info('Empty statement')
        return None


def get_statement(url, one_time_token="", signature=""):
    headers = {
        'Authorization': 'Bearer ' + token,
        'User-Agent': 'tw-statements-sca',
        'Content-Type': 'application/json'}
    if one_time_token != "":
        headers['x-2fa-approval'] = one_time_token
        headers['X-Signature'] = signature

    print('GET', url)

    r = http.request('GET', url, headers=headers, body={}, retries=False)

    print('status:', r.status)

    if r.status == 200 or r.status == 201:
        return json.loads(r.data)
    elif r.status == 403 and r.getheader('x-2fa-approval') is not None:
        one_time_token = r.getheader('x-2fa-approval')
        signature = do_sca_challenge(one_time_token)
        get_statement(url, one_time_token, signature)
    else:
        logger.error(f'failed: {r.status}')
        logger.error(r.data)
        raise Exception('failed call')


def do_sca_challenge(one_time_token):
    logger.info('doing sca challenge')

    # Read the private key file as bytes.
    with open(private_key_path, 'rb') as f:
        private_key_data = f.read()

    private_key = rsa.PrivateKey.load_pkcs1(private_key_data, 'PEM')

    # Use the private key to sign the one-time-token that was returned
    # in the x-2fa-approval header of the HTTP 403.
    signed_token = rsa.sign(
        one_time_token.encode('ascii'),
        private_key,
        'SHA-256')

    # Encode the signed message as friendly base64 format for HTTP
    # headers.
    signature = base64.b64encode(signed_token).decode('ascii')

    return signature
