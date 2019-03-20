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

import sys

from marketplace_addressing.addresser import address_is
from marketplace_addressing.addresser import AddressSpace


TABLE_NAMES = {
    AddressSpace.ACCOUNT: 'accounts',
    AddressSpace.ASSET: 'assets',
    AddressSpace.HOLDING: 'holdings',
    AddressSpace.OFFER: 'offers'
}

SECONDARY_INDEXES = {
    AddressSpace.ACCOUNT: 'public_key',
    AddressSpace.ASSET: 'name',
    AddressSpace.HOLDING: 'id',
    AddressSpace.OFFER: 'id'
}


def get_updater(database, block_num):
    """Returns an updater function, which can be used to update the database
    appropriately for a particular address/data combo.
    """
    return lambda adr, rsc: _update(database, block_num, adr, rsc)


def _update(database, block_num, address, resource):
    data_type = address_is(address)

    resource['start_block_num'] = block_num
    resource['end_block_num'] = sys.maxsize

    try:
        table_query = database.get_table(TABLE_NAMES[data_type])
        seconday_index = SECONDARY_INDEXES[data_type]
    except KeyError:
        raise TypeError('Unknown data type: {}'.format(data_type))

    query = table_query\
        .get_all(resource[seconday_index], index=seconday_index)\
        .filter({'end_block_num': sys.maxsize})\
        .update({'end_block_num': block_num})\
        .merge(table_query.insert(resource).without('replaced'))

    return database.run_query(query)
