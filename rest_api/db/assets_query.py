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

async def fetch_all_asset_resources(conn):
    return await r.table('assets')\
        .filter((fetch_latest_block_num() >= r.row['start_block_num'])
                & (fetch_latest_block_num() < r.row['end_block_num']))\
        .map(lambda asset: (asset['description'] == "").branch(
            asset.without('description'), asset))\
        .map(lambda asset: (asset['rules'] == []).branch(
            asset, asset.merge(parse_rules(asset['rules']))))\
        .without('start_block_num', 'end_block_num', 'delta_id')\
        .coerce_to('array').run(conn)


async def fetch_asset_resource(conn, name):
    try:
        return await r.table('assets')\
            .get_all(name, index='name')\
            .max('start_block_num')\
            .do(lambda asset: (asset['description'] == "").branch(
                asset.without('description'), asset))\
            .do(lambda asset: (asset['rules'] == []).branch(
                asset, asset.merge(parse_rules(asset['rules']))))\
            .without('start_block_num', 'end_block_num', 'delta_id')\
            .run(conn)
    except ReqlNonExistenceError:
        raise ApiBadRequest(
            "Bad Request: "
            "No asset with the name {} exists".format(name))
