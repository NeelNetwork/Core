#   Copyright (c) 2019 Neel Network

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#   ---------------------------------------------------------------------------

import bcrypt

from itsdangerous import BadSignature

from sanic import Blueprint
from sanic import response

from sawtooth_signing import CryptoFactory

from api.authorization import authorized
from api import common
from api import messaging
from api.errors import ApiBadRequest
from api.errors import ApiInternalError

from db import accounts_query
from db import auth_query

from marketplace_transaction import transaction_creation


ACCOUNTS_BP = Blueprint('accounts')


@ACCOUNTS_BP.get('accounts/create')
async def create_account(request):
    """Creates a new Account and corresponding authorization token"""
    # required_fields = ['email', 'password']
    # common.validate_fields(required_fields, request.json)

    privateKey = request.app.config.CONTEXT.new_random_private_key()
    signer = CryptoFactory(request.app.config.CONTEXT).new_signer(privateKey)
    public_key = signer.get_public_key().as_hex()
    private_key = signer.get_public_key().as_hex()

    # auth_entry = _create_auth_dict(
    #     request, public_key, private_key.as_hex())
    # await auth_query.create_auth_entry(request.app.config.DB_CONN, auth_entry)

    # account = _create_account_dict(request.json, public_key)

    # batches, batch_id = transaction_creation.create_account(
    #     txn_key=signer,
    #     batch_key=request.app.config.SIGNER,
    #     label=account.get('label'),
    #     description=account.get('description'))

    # await messaging.send(
    #     request.app.config.VAL_CONN,
    #     request.app.config.TIMEOUT,
    #     batches)

    # try:
    #     await messaging.check_batch_status(
    #         request.app.config.VAL_CONN, batch_id)
    # except (ApiBadRequest, ApiInternalError) as err:
    #     await auth_query.remove_auth_entry(
    #         request.app.config.DB_CONN, request.json.get('email'))
    #     raise err

    # token = common.generate_auth_token(
    #     request.app.config.SECRET_KEY,
    #     account.get('email'),
    #     public_key)

    print('private_key', private_key)
    print('public_key', public_key)
    return response.json(
        {
            'private_key': private_key,
            'public_key': public_key
        })


@ACCOUNTS_BP.get('accounts')
async def get_all_accounts(request):
    """Fetches complete details of all Accounts in state"""
    account_resources = await accounts_query.fetch_all_account_resources(
        request.app.config.DB_CONN)
    return response.json(account_resources)


@ACCOUNTS_BP.get('accounts/<key>')
async def get_account(request, key):
    """Fetches the details of particular Account in state"""
    try:
        auth_key = common.deserialize_auth_token(
            request.app.config.SECRET_KEY,
            request.token).get('public_key')
    except (BadSignature, TypeError):
        auth_key = None
    account_resource = await accounts_query.fetch_account_resource(
        request.app.config.DB_CONN, key, auth_key)
    return response.json(account_resource)


@ACCOUNTS_BP.patch('accounts')
@authorized()
async def update_account_info(request):
    """Updates auth information for the authorized account"""
    token = common.deserialize_auth_token(
        request.app.config.SECRET_KEY, request.token)

    update = {}
    if request.json.get('password'):
        update['hashed_password'] = bcrypt.hashpw(
            bytes(request.json.get('password'), 'utf-8'), bcrypt.gensalt())
    if request.json.get('email'):
        update['email'] = request.json.get('email')

    if update:
        updated_auth_info = await auth_query.update_auth_info(
            request.app.config.DB_CONN,
            token.get('email'),
            token.get('public_key'),
            update)
        new_token = common.generate_auth_token(
            request.app.config.SECRET_KEY,
            updated_auth_info.get('email'),
            updated_auth_info.get('publicKey'))
    else:
        updated_auth_info = await accounts_query.fetch_account_resource(
            request.app.config.DB_CONN,
            token.get('public_key'),
            token.get('public_key'))
        new_token = request.token

    return response.json(
        {
            'authorization': new_token,
            'account': updated_auth_info
        })


def _create_account_dict(body, public_key):
    keys = ['label', 'description', 'email']

    account = {k: body[k] for k in keys if body.get(k) is not None}

    account['publicKey'] = public_key
    account['holdings'] = []

    return account


def _create_auth_dict(request, public_key, private_key):
    auth_entry = {
        'public_key': public_key,
        'email': request.json['email']
    }

    auth_entry['encrypted_private_key'] = common.encrypt_private_key(
        request.app.config.AES_KEY, public_key, private_key)
    auth_entry['hashed_password'] = bcrypt.hashpw(
        bytes(request.json.get('password'), 'utf-8'), bcrypt.gensalt())

    return auth_entry
