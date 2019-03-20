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

import logging
import rethinkdb as re

r = re.RethinkDB()
LOGGER = logging.getLogger(__name__)


class Database(object):
    """Simple object for managing a connection to a rethink database
    """
    def __init__(self, host, port, name):
        self._host = host
        self._port = port
        self._name = name
        self._conn = None

    def connect(self):
        """Initializes a connection to the database
        """
        LOGGER.debug('Connecting to database: %s:%s', self._host, self._port)
        self._conn = r.connect(host=self._host, port=self._port)

    def disconnect(self):
        """Closes the connection to the database
        """
        LOGGER.debug('Disconnecting from database')
        self._conn.close()

    def fetch(self, table_name, primary_id):
        """Fetches a single resource by its primary id
        """
        return r.db(self._name).table(table_name)\
            .get(primary_id).run(self._conn)

    def insert(self, table_name, docs):
        """Inserts a document or a list of documents into the specified table
        in the database
        """
        return r.db(self._name).table(table_name).insert(docs).run(self._conn)

    def last_known_blocks(self, count):
        """Fetches the ids of the specified number of most recent blocks
        """
        cursor = r.db(self._name).table('blocks')\
            .order_by('block_num')\
            .get_field('block_id')\
            .run(self._conn)

        return list(cursor)[-count:]

    def drop_fork(self, block_num):
        """Deletes all resources from a particular block_num
        """
        block_results = r.db(self._name).table('blocks')\
            .filter(lambda rsc: rsc['block_num'].ge(block_num))\
            .delete()\
            .run(self._conn)

        resource_results = r.db(self._name).table_list()\
            .for_each(
                lambda table_name: r.branch(
                    r.eq(table_name, 'blocks'),
                    [],
                    r.eq(table_name, 'auth'),
                    [],
                    r.db(self._name).table(table_name)
                    .filter(lambda rsc: rsc['start_block_num'].ge(block_num))
                    .delete()))\
            .run(self._conn)

        return {k: v + resource_results[k] for k, v in block_results.items()}

    def get_table(self, table_name):
        """Returns a rethink table query, which can be added to, and
        eventually run with run_query
        """
        return r.db(self._name).table(table_name)

    def run_query(self, query):
        """Takes a query based on get_table, and runs it.
        """
        return query.run(self._conn)
