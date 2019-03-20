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

from marketplace_processor.protobuf import offer_pb2


def handle_close_offer(close_offer, header, state):
    """Handle Offer closure.

    Args:
        close_offer (CloseOffer): The transaction.
        header (TransactionHeader): The TransactionHeader.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        - InvalidTransaction
            - The Offer doesn't exist.
            - The txn signer is not within the owners of the Offer.
    """

    offer = state.get_offer(close_offer.id)

    if not offer:
        raise InvalidTransaction(
            "Failed to close offer, the offer id {} "
            "does not reference an Offer.".format(
                close_offer.id))

    if not offer.status == offer_pb2.Offer.OPEN:
        raise InvalidTransaction(
            "Failed to close offer, the Offer {} is {} "
            "not open".format(offer.id, offer.status))

    if header.signer_public_key not in offer.owners:
        raise InvalidTransaction(
            "Failed to close offer, the txn signer {} "
            "is not a member of the offer's owners.".format(
                header.signer_public_key))

    state.close_offer(close_offer.id)
