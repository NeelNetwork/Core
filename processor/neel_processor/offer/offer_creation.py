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

from marketplace_processor.protobuf import rule_pb2


def handle_offer_creation(create_offer, header, state):
    """Handle Offer creation.

    Args:
        create_offer (CreateOffer): The transaction.
        header (TransactionHeader): The header of the Transaction.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        InvalidTransaction
            - There is already an Offer with the same identifier.
            - The txn signer does not have an Account.
            - Either the source or target Holding account is not the signer.
            - The source is unset.
            - The source_quantity is unset or 0.
            - The target or target_quantity are set while the other is unset.
            - The source is not a holding.
            - THe target is not a holding.

    """

    if state.get_offer(identifier=create_offer.id):
        raise InvalidTransaction(
            "Failed to create Offer, id {} already exists.".format(
                create_offer.id))

    if not state.get_account(public_key=header.signer_public_key):
        raise InvalidTransaction(
            "Failed to create offer, transaction signer {} does "
            "not have an Account.".format(header.signer_public_key))

    if not create_offer.source:
        raise InvalidTransaction(
            "Failed to create Offer, Offer source is not specified.")

    if create_offer.source_quantity == 0:
        raise InvalidTransaction("Failed to create Offer, source_quantity "
                                 "was unset or 0")

    source_holding = state.get_holding(identifier=create_offer.source)
    if not source_holding:
        raise InvalidTransaction(
            "Failed to create Offer, Holding id {} listed as source "
            "does not refer to a Holding.".format(create_offer.source))

    if not source_holding.account == header.signer_public_key:
        raise InvalidTransaction(
            "Failed to create Offer, source Holding account {} not "
            "owned by txn signer {}".format(source_holding.account,
                                            header.signer_public_key))
    source_asset = state.get_asset(source_holding.asset)
    if _is_not_transferable(source_asset, header.signer_public_key):
        raise InvalidTransaction(
            "Failed to create Offer, source asset {} are not "
            "transferable".format(source_asset.name))

    if create_offer.target and not create_offer.target_quantity or \
            create_offer.target_quantity and not create_offer.target:
        raise InvalidTransaction("Failed to create Offer, target and "
                                 "target_quantity must both be set or "
                                 "both unset.")

    if create_offer.target:
        target_holding = state.get_holding(identifier=create_offer.target)
        if not target_holding:
            raise InvalidTransaction(
                "Failed to create Offer, Holding id {} listed as target "
                "does not refer to a Holding.".format(create_offer.target))

        if not target_holding.account == header.signer_public_key:
            raise InvalidTransaction(
                "Failed to create Offer, target Holding account {} not "
                "owned by txn signer {}".format(target_holding.account,
                                                header.signer_public_key))
        target_asset = state.get_asset(target_holding.asset)
        if _is_not_transferable(target_asset, header.signer_public_key):
            raise InvalidTransaction(
                "Failed to create Offer, target asset {} is not "
                "transferable".format(target_asset.name))

    state.set_create_offer(
        identifier=create_offer.id,
        label=create_offer.label,
        description=create_offer.description,
        owners=[header.signer_public_key],
        source=create_offer.source,
        source_quantity=create_offer.source_quantity,
        target=create_offer.target,
        target_quantity=create_offer.target_quantity,
        rules=create_offer.rules)


def _is_not_transferable(asset, owner_public_key):
    if _has_rule(asset.rules, rule_pb2.Rule.NOT_TRANSFERABLE) \
            and owner_public_key not in asset.owners:
        return True
    return False


def _has_rule(rules, rule_type):
    for rule in rules:
        if rule.type == rule_type:
            return True
    return False
