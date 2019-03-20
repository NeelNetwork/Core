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

import sys
import argparse
import logging

from marketplace_ledger_sync.database import Database
from marketplace_ledger_sync.subscriber import Subscriber
from marketplace_ledger_sync.deltas.handlers import get_events_handler


LOGGER = logging.getLogger(__name__)

# State Delta catches up based on the first valid ID it finds, which is
# likely genesis, defeating the purpose. Rewind just 15 blocks to handle forks.
KNOWN_COUNT = 15


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase level of output sent to stderr')
    parser.add_argument('--validator',
                        help='The url of the validator to sync with',
                        default='tcp://localhost:4004')
    parser.add_argument('--db-host',
                        help='The host of the database to connect to',
                        default='localhost')
    parser.add_argument('--db-port',
                        help='The port of the database to connect to',
                        default='28015')
    parser.add_argument('--db-name',
                        help='The name of the database to use',
                        default='marketplace')
    return parser.parse_args(args)


def init_logger(level):
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    if level == 1:
        logger.setLevel(logging.INFO)
    elif level > 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARN)


def main():
    try:
        opts = parse_args(sys.argv[1:])
        init_logger(opts.verbose)

        LOGGER.info('Starting Ledger Sync...')

        database = Database(opts.db_host, opts.db_port, opts.db_name)
        database.connect()

        subscriber = Subscriber(opts.validator)
        subscriber.add_handler(get_events_handler(database))

        known_blocks = database.last_known_blocks(KNOWN_COUNT)
        subscriber.start(known_blocks)

    except KeyboardInterrupt:
        sys.exit(0)

    except Exception as err:  # pylint: disable=broad-except
        LOGGER.exception(err)
        sys.exit(1)

    finally:
        try:
            subscriber.stop()
        except UnboundLocalError:
            pass

        try:
            database.disconnect()
        except UnboundLocalError:
            pass

        LOGGER.info('Ledger Sync shut down successfully')
