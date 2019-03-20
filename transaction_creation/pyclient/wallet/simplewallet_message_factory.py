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
'''
This file is used for automated testing of the simplewallet client.
'''

from sawtooth_processor_test.message_factory import MessageFactory

class SimplewalletMessageFactory(object):
    def __init__(self, signer=None):
        self._factory = MessageFactory(
            family_name="simplewallet",
            family_version="1.0",
            namespace=MessageFactory.sha512("simplewallet".encode("utf-8"))[0:6],
            signer=signer)

    def get_public_key(self):
        return self._factory.get_public_key()

    def _make_address(self):
        return self._factory.namespace + \
            self._factory.sha512(get_public_key())[0:64]

    def create_tp_register(self):
        return self._factory.create_tp_register()

    def create_tp_response(self, status):
        return self._factory.create_tp_response(status)

    def _create_txn(self, txn_function, action, value=None):
        payload = ",".join([
            str(action), str(value)
        ]).encode()

        addresses = [self._make_address()]

        return txn_function(payload, addresses, addresses, [])

    def create_tp_process_request(self, action, value=None):
        txn_function = self._factory.create_tp_process_request
        return self._create_txn(txn_function, action, value)

    def create_transaction(self, action, value=None):
        txn_function = self._factory.create_transaction
        return self._create_txn(txn_function, action, value)

    def create_get_request(self):
        addresses = [self._make_address()]
        return self._factory.create_get_request(addresses)

    def create_set_request(self, value):
        address = self._make_address()
        data = None
        if value is not None:
            data = str(value).encode()
        else:
            data = None
        return self._factory.create_set_request({address: data})

    def create_get_response(self, value):
        address = self._make_address()
        data = None
        if value is not None:
            data = str(value).encode()
        else:
            data = None
        return self._factory.create_get_response({address: data})

    def create_set_response(self, game):
        addresses = [self._make_address()]
        return self._factory.create_set_response(addresses)

