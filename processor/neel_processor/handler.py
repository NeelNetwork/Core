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
#   --------------------------------------------------------------------------

from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.handler import TransactionHandler

from marketplace_addressing import addresser

from marketplace_processor.account import account_creation
from marketplace_processor.asset import asset_creation
from marketplace_processor.offer import offer_acceptance
from marketplace_processor.offer import offer_closure
from marketplace_processor.offer import offer_creation
from marketplace_processor.marketplace_payload import MarketplacePayload
from marketplace_processor.marketplace_state import MarketplaceState


class MarketplaceHandler(TransactionHandler):

    @property
    def family_name(self):
        return addresser.FAMILY_NAME

    @property
    def namespaces(self):
        return [addresser.NS]

    @property
    def family_versions(self):
        return ['1.0']

    def apply(self, transaction, context):

        state = MarketplaceState(context=context, timeout=2)
        payload = MarketplacePayload(payload=transaction.payload)

        if payload.is_create_account():
            account_creation.handle_account_creation(
                payload.create_account(),
                header=transaction.header,
                state=state)
        elif payload.is_create_asset():
            asset_creation.handle_asset_creation(
                payload.create_asset(),
                header=transaction.header,
                state=state)
        elif payload.is_create_offer():
            offer_creation.handle_offer_creation(
                payload.create_offer(),
                header=transaction.header,
                state=state)
        elif payload.is_accept_offer():
            offer_acceptance.handle_accept_offer(
                payload.accept_offer(),
                header=transaction.header,
                state=state)
        elif payload.is_close_offer():
            offer_closure.handle_close_offer(
                payload.close_offer(),
                header=transaction.header,
                state=state)

        else:
            raise InvalidTransaction("Transaction payload type unknown.")
