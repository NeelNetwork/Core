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

import unittest
from uuid import uuid4

from marketplace_addressing import addresser


class AddresserTest(unittest.TestCase):

    def test_asset_address(self):

        asset_address = addresser.make_asset_address(uuid4().hex)

        self.assertEqual(len(asset_address), 70, "The address is valid.")

        self.assertEqual(addresser.address_is(asset_address),
                         addresser.AddressSpace.ASSET,
                         "The address is correctly identified as an Asset.")

    def test_offer_address(self):
        offer_address = addresser.make_offer_address(uuid4().hex)

        self.assertEqual(len(offer_address), 70, "The address is valid.")

        self.assertEqual(addresser.address_is(offer_address),
                         addresser.AddressSpace.OFFER,
                         "The address is correctly identified as an Offer.")

    def test_account_address(self):
        account_address = addresser.make_account_address(uuid4().hex)

        self.assertEqual(len(account_address), 70, "The address is valid.")

        self.assertEqual(addresser.address_is(account_address),
                         addresser.AddressSpace.ACCOUNT,
                         "The address is correctly identified as an Account.")

    def test_holding_address(self):
        holding_address = addresser.make_holding_address(uuid4().hex)

        self.assertEqual(len(holding_address), 70, "The address is valid.")

        self.assertEqual(addresser.address_is(holding_address),
                         addresser.AddressSpace.HOLDING,
                         "The address is correctly identified as an Holding.")

    def test_offer_history_address(self):
        offer_history_address = addresser.make_offer_account_address(
            uuid4().hex,
            uuid4().hex)

        self.assertEqual(len(offer_history_address), 70, "The address is valid")
