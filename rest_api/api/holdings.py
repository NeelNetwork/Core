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

from uuid import uuid4

from sanic import Blueprint
from sanic import response

from api import common
from api import messaging
from api.authorization import authorized

from marketplace_transaction import transaction_creation


HOLDINGS_BP = Blueprint('holdings')


@HOLDINGS_BP.post('holdings')
@authorized()
async def create_holding(request):
    """Creates a new Holding for the authorized Account"""
    required_fields = ['asset']
    common.validate_fields(required_fields, request.json)

    holding = _create_holding_dict(request)
    signer = await common.get_signer(request)

    batches, batch_id = transaction_creation.create_holding(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        identifier=holding['id'],
        label=holding.get('label'),
        description=holding.get('description'),
        asset=holding['asset'],
        quantity=holding['quantity'])

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    return response.json(holding)


def _create_holding_dict(request):
    keys = ['label', 'description', 'asset', 'quantity']
    body = request.json

    holding = {k: body[k] for k in keys if body.get(k) is not None}

    if holding.get('quantity') is None:
        holding['quantity'] = 0

    holding['id'] = str(uuid4())

    return holding
