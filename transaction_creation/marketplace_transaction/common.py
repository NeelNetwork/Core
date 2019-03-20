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

import hashlib
from uuid import uuid4

from sawtooth_rest_api.protobuf import batch_pb2
from sawtooth_rest_api.protobuf import transaction_pb2

from marketplace_addressing import addresser


def wrap_payload_in_txn_batch(txn_key, payload, header, batch_key):
    """Takes the serialized RBACPayload and creates a batch_list, batch
    signature tuple.
    Args:
        txn_key (sawtooth_signing.Signer): The txn signer's key pair.
        payload (bytes): The serialized RBACPayload.
        header (bytes): The serialized TransactionHeader.
        batch_key (sawtooth_signing.Signer): The batch signer's key pair.
    Returns:
        tuple
            The zeroth element is a BatchList, and the first element is
            the batch header_signature.
    """

    transaction = transaction_pb2.Transaction(
        payload=payload,
        header=header,
        header_signature=txn_key.sign(header))

    batch_header = batch_pb2.BatchHeader(
        signer_public_key=batch_key.get_public_key().as_hex(),
        transaction_ids=[transaction.header_signature]).SerializeToString()

    batch = batch_pb2.Batch(
        header=batch_header,
        header_signature=batch_key.sign(batch_header),
        transactions=[transaction])

    return [batch], batch.header_signature


def make_header_and_batch(payload, inputs, outputs, txn_key, batch_key):

    header = make_header(
        inputs=inputs,
        outputs=outputs,
        payload_sha512=hashlib.sha512(
            payload.SerializeToString()).hexdigest(),
        signer_pubkey=txn_key.get_public_key().as_hex(),
        batcher_pubkey=batch_key.get_public_key().as_hex())

    return wrap_payload_in_txn_batch(
        txn_key=txn_key,
        payload=payload.SerializeToString(),
        header=header.SerializeToString(),
        batch_key=batch_key)


def make_header(inputs,
                outputs,
                payload_sha512,
                signer_pubkey,
                batcher_pubkey):
    header = transaction_pb2.TransactionHeader(
        inputs=inputs,
        outputs=outputs,
        batcher_public_key=batcher_pubkey,
        dependencies=[],
        family_name=addresser.FAMILY_NAME,
        family_version='1.0',
        nonce=uuid4().hex,
        signer_public_key=signer_pubkey,
        payload_sha512=payload_sha512)
    return header
