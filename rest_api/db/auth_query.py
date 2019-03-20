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

import logging

import rethinkdb as re

from api.errors import ApiBadRequest


r = re.RethinkDB()


LOGGER = logging.getLogger(__name__)


async def create_auth_entry(conn, auth_entry):
    result = await r.table('auth').insert(auth_entry).run(conn)
    if result.get('errors') > 0 and \
       "Duplicate primary key `email`" in result.get('first_error'):
        raise ApiBadRequest("A user with that email already exists")


async def remove_auth_entry(conn, email):
    await r.table('auth').get(email).delete().run(conn)


async def fetch_info_by_email(conn, email):
    return await r.table('auth').get(email).run(conn)


async def update_auth_info(conn, email, public_key, update):
    result = await r.table('auth')\
        .get(email)\
        .do(lambda auth_info: r.expr(update.get('email')).branch(
            r.expr(r.table('auth').insert(auth_info.merge(update),
                                          return_changes=True)),
            r.table('auth').get(email).update(update, return_changes=True)))\
        .do(lambda auth_info: auth_info['errors'].gt(0).branch(
            auth_info,
            auth_info['changes'][0]['new_val'].pluck('email')))\
        .merge(_fetch_account_info(public_key))\
        .run(conn)
    if result.get('errors'):
        if "Duplicate primary key `email`" in result.get('first_error'):
            raise ApiBadRequest(
                "Bad Request: A user with that email already exists")
        else:
            raise ApiBadRequest(
                "Bad Request: {}".format(result.get('first_error')))
    if update.get('email'):
        await remove_auth_entry(conn, email)
    return result


def _fetch_account_info(public_key):
    return r.table('accounts')\
        .get_all(public_key, index='public_key')\
        .max('start_block_num')\
        .do(lambda account: account.merge(
            {'publicKey': account['public_key']}))\
        .do(lambda account: (account['label'] == "").branch(
            account.without('label'), account))\
        .do(lambda account: (account['description'] == "").branch(
            account.without('description'), account))\
        .without('public_key', 'delta_id',
                 'start_block_num', 'end_block_num')
