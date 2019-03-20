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

import re
import logging

from sawtooth_sdk.protobuf.transaction_receipt_pb2 import StateChangeList

from marketplace_ledger_sync.deltas.decoding import data_to_dicts
from marketplace_ledger_sync.deltas.updating import get_updater
from marketplace_addressing.addresser import NS as NAMESPACE


NS_REGEX = re.compile('^{}'.format(NAMESPACE))
LOGGER = logging.getLogger(__name__)


def get_events_handler(database):
    """Returns a events handler with a reference to a specific Database object.
    The handler takes a list of events and updates the Database appropriately.
    """
    return lambda events: _handle_events(database, events)


def _handle_events(database, events):
    block_num, block_id = _parse_new_block(events)

    is_duplicate = _resolve_if_forked(database, block_num, block_id)
    if is_duplicate:
        return

    changes = _parse_state_changes(events)
    _apply_state_changes(database, changes, block_num)

    _insert_new_block(database, block_num, block_id)


def _parse_new_block(events):
    try:
        block_attr = next(e.attributes for e in events
                          if e.event_type == 'sawtooth/block-commit')
    except StopIteration:
        return None, None

    block_num = int(next(a.value for a in block_attr if a.key == 'block_num'))
    block_id = next(a.value for a in block_attr if a.key == 'block_id')
    LOGGER.debug('Handling deltas for block: %s', block_id)
    return block_num, block_id


def _parse_state_changes(events):
    try:
        change_data = next(e.data for e in events
                           if e.event_type == 'sawtooth/state-delta')
    except StopIteration:
        return []

    state_change_list = StateChangeList()
    state_change_list.ParseFromString(change_data)
    return [c for c in state_change_list.state_changes
            if NS_REGEX.match(c.address)]


def _resolve_if_forked(database, block_num, block_id):
    old_block = database.fetch('blocks', block_num)
    if old_block is not None:
        if old_block['block_id'] == block_id:
            return True  # this block is a duplicate
        drop_results = database.drop_fork(block_num)
        if drop_results['deleted'] == 0:
            LOGGER.warning(
                'Failed to drop forked resources since block: %s',
                block_num)
    return False


def _apply_state_changes(database, changes, block_num):
    update = get_updater(database, block_num)
    for change in changes:
        resources = data_to_dicts(change.address, change.value)
        for resource in resources:
            update_results = update(change.address, resource)
            if update_results['inserted'] == 0:
                LOGGER.warning(
                    'Failed to insert resource from address: %s',
                    change.address)


def _insert_new_block(database, block_num, block_id):
    new_block = {'block_num': block_num, 'block_id': block_id}
    block_results = database.insert('blocks', new_block)
    if block_results['inserted'] == 0:
        LOGGER.warning('Failed to insert block #%s: %s', block_num, block_id)
