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

import rethinkdb as re
from rethinkdb.errors import ReqlNonExistenceError

from api.errors import ApiBadRequest

from db.common import fetch_latest_block_num
from db.common import parse_rules


r = re.RethinkDB()

async def fetch_all_offer_resources(conn, query_params):
    return await r.table('offers')\
        .filter((fetch_latest_block_num() >= r.row['start_block_num'])
                & (fetch_latest_block_num() < r.row['end_block_num']))\
        .filter(query_params)\
        .map(lambda offer: (offer['label'] == "").branch(
            offer.without('label'), offer))\
        .map(lambda offer: (offer['description'] == "").branch(
            offer.without('description'), offer))\
        .map(lambda offer: offer.merge(
            {'sourceQuantity': offer['source_quantity']}))\
        .map(lambda offer: (offer['target'] == "").branch(
            offer.without('target'), offer))\
        .map(lambda offer: (offer['target_quantity'] == "").branch(
            offer,
            offer.merge({'targetQuantity': offer['target_quantity']})))\
        .map(lambda offer: (offer['rules'] == []).branch(
            offer, offer.merge(parse_rules(offer['rules']))))\
        .without('delta_id', 'start_block_num', 'end_block_num',
                 'source_quantity', 'target_quantity')\
        .coerce_to('array').run(conn)


async def fetch_offer_resource(conn, offer_id):
    try:
        return await r.table('offers')\
            .get_all(offer_id, index='id')\
            .max('start_block_num')\
            .do(lambda offer: (offer['label'] == "").branch(
                offer.without('label'), offer))\
            .do(lambda offer: (offer['description'] == "").branch(
                offer.without('description'), offer))\
            .merge({'sourceQuantity': r.row['source_quantity']})\
            .do(lambda offer: (offer['target'] == "").branch(
                offer.without('target'), offer))\
            .do(lambda offer: (offer['target_quantity'] == "").branch(
                offer,
                offer.merge({'targetQuantity': offer['target_quantity']})))\
            .do(lambda offer: (offer['rules'] == []).branch(
                offer, offer.merge(parse_rules(offer['rules']))))\
            .without('delta_id', 'start_block_num', 'end_block_num',
                     'source_quantity', 'target_quantity')\
            .run(conn)
    except ReqlNonExistenceError:
        raise ApiBadRequest("No offer with the id {} exists".format(offer_id))
