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

from db.common import fetch_holdings
from db.common import fetch_latest_block_num

r = re.RethinkDB()

async def fetch_all_account_resources(conn):
    return await r.table('accounts')\
        .filter((fetch_latest_block_num() >= r.row['start_block_num'])
                & (fetch_latest_block_num() < r.row['end_block_num']))\
        .map(lambda account: account.merge(
            {'publicKey': account['public_key']}))\
        .map(lambda account: account.merge(
            {'holdings': fetch_holdings(account['holdings'])}))\
        .map(lambda account: (account['label'] == "").branch(
            account.without('label'), account))\
        .map(lambda account: (account['description'] == "").branch(
            account.without('description'), account))\
        .without('public_key', 'delta_id',
                 'start_block_num', 'end_block_num')\
        .coerce_to('array').run(conn)


async def fetch_account_resource(conn, public_key, auth_key):
    try:
        return await r.table('accounts')\
            .get_all(public_key, index='public_key')\
            .max('start_block_num')\
            .merge({'publicKey': r.row['public_key']})\
            .merge({'holdings': fetch_holdings(r.row['holdings'])})\
            .do(lambda account: (r.expr(auth_key).eq(public_key)).branch(
                account.merge(_fetch_email(public_key)), account))\
            .do(lambda account: (account['label'] == "").branch(
                account.without('label'), account))\
            .do(lambda account: (account['description'] == "").branch(
                account.without('description'), account))\
            .without('public_key', 'delta_id',
                     'start_block_num', 'end_block_num')\
            .run(conn)
    except ReqlNonExistenceError:
        raise ApiBadRequest(
            "No account with the public key {} exists".format(public_key))


def _fetch_email(public_key):
    return r.table('auth')\
        .get_all(public_key, index='public_key')\
        .pluck('email')\
        .coerce_to('array')[0]
