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

from marketplace_processor.protobuf import payload_pb2


class MarketplacePayload(object):

    def __init__(self, payload):
        self._transaction = payload_pb2.TransactionPayload()
        self._transaction.ParseFromString(payload)

    def create_account(self):
        """Returns the value set in the create_account.

        Returns:
            payload_pb2.CreateAccount
        """

        return self._transaction.create_account

    def is_create_account(self):

        create_account = payload_pb2.TransactionPayload.CREATE_ACCOUNT

        return self._transaction.payload_type == create_account

    
    def create_asset(self):
        """Returns the value set in the create_asset.

        Returns:
            payload_pb2.CreateAsset
        """

        return self._transaction.create_asset

    def is_create_asset(self):

        create_asset = payload_pb2.TransactionPayload.CREATE_ASSET

        return self._transaction.payload_type == create_asset

    def create_offer(self):
        """Returns the value set in the create_offer.

        Returns:
            payload_pb2.CreateOffer
        """

        return self._transaction.create_offer

    def is_create_offer(self):

        create_offer = payload_pb2.TransactionPayload.CREATE_OFFER

        return self._transaction.payload_type == create_offer

    def accept_offer(self):
        """Returns the value set in accept_offer.

        Returns:
            payload_pb2.AcceptOffer
        """

        return self._transaction.accept_offer

    def is_accept_offer(self):

        accept_offer = payload_pb2.TransactionPayload.ACCEPT_OFFER

        return self._transaction.payload_type == accept_offer

    def close_offer(self):
        """Returns the value set in close_offer.

        Returns:
            payload_pb2.CloseOffer
        """

        return self._transaction.close_offer

    def is_close_offer(self):

        close_offer = payload_pb2.TransactionPayload.CLOSE_OFFER

        return self._transaction.payload_type == close_offer
