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

from urllib.parse import unquote

from sanic import Blueprint
from sanic import response
from sawtooth_signing import CryptoFactory
from api.authorization import authorized
from api import common
from api import messaging

from db import assets_query

from marketplace_transaction import transaction_creation


ASSETS_BP = Blueprint('assets')


@ASSETS_BP.post('assets')
# @authorized()
async def create_asset(request):
    """Creates a new Asset in state"""
    required_fields = ['name' , 'public_key' , 'private_key']
    common.validate_fields(required_fields, request.json)

    # signer = await common.get_signer(request)
    asset = _create_asset_dict(request.json, request.json['public_key'])
    signer = CryptoFactory(request.app.config.CONTEXT).new_signer(request.json['private_key'])

    batches, batch_id = transaction_creation.create_asset(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        name=asset.get('name'),
        description=asset.get('description'),
        rules=asset.get('rules'))

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    if asset.get('rules'):
        asset['rules'] = request.json['rules']

    return response.json(asset)


@ASSETS_BP.get('assets')
async def get_all_assets(request):
    """Fetches complete details of all Assets in state"""
    asset_resources = await assets_query.fetch_all_asset_resources(
        request.app.config.DB_CONN)
    return response.json(asset_resources)


@ASSETS_BP.get('assets/<name>')
async def get_asset(request, name):
    """Fetches the details of particular Asset in state"""
    decoded_name = unquote(name)
    asset_resource = await assets_query.fetch_asset_resource(
        request.app.config.DB_CONN, decoded_name)
    return response.json(asset_resource)


def _create_asset_dict(body, public_key):
    keys = ['name', 'description']

    asset = {k: body[k] for k in keys if body.get(k) is not None}
    asset['owners'] = [public_key]

    if body.get('rules'):
        asset['rules'] = common.proto_wrap_rules(body['rules'])

    return asset
