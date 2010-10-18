###
# OTCOrderBook - supybot plugin to keep an order book from irc
# Copyright (C) 2010, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import conf

import sqlite3
import time
import os.path

class OTCOrderDB(object):
    def __init__(self, filename):
        self.filename = filename
        self.db = None

    def open(self):
        if os.path.exists(self.filename):
            db = sqlite3.connect(self.filename, check_same_thread = False)
            db.text_factory = str
            self.db = db
            return
        
        db = sqlite3.connect(self.filename, check_same_thread = False)
        db.text_factory = str
        self.db = db
        cursor = self.db.cursor()
        cursor.execute("""CREATE TABLE orders (
                          id INTEGER PRIMARY KEY,
                          created_at INTEGER,
                          refreshed_at INTEGER,
                          buysell TEXT,
                          nick TEXT,
                          host TEXT,
                          btcamount REAL,
                          price REAL,
                          othercurrency TEXT,
                          notes TEXT)
                          """)
        self.db.commit()
        return

    def close(self):
        self.db.close()

    def get(self, host, id=None):
        cursor = self.db.cursor()
        if id is None:
            cursor.execute("""SELECT * FROM orders WHERE host=?""", (host,))
        else:
            cursor.execute("""SELECT * FROM orders WHERE host=? AND
                           id=?""", (host, id))
        return cursor.fetchall()

    def deleteExpired(self, expiry):
        cursor = self.db.cursor()
        timestamp = time.time()
        cursor.execute("""DELETE FROM orders WHERE refreshed_at + ? < ?""",
                       (expiry, timestamp))
        self.db.commit()

    def getCurrencyBook(self, currency):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM orders WHERE othercurrency = ?
                       ORDER BY price""",
                       (currency,))
        return cursor.fetchall()

    def buy(self, nick, host, btcamount, price, othercurrency, notes):
        cursor = self.db.cursor()
        timestamp = time.time()
        cursor.execute("""INSERT INTO orders VALUES
                       (NULL, ?, ?, "BUY", ?, ?, ?, ?, ?, ?)""",
                       (timestamp, timestamp, nick, host, btcamount, price,
                        othercurrency, notes))
        self.db.commit()

    def sell(self, nick, host, btcamount, price, othercurrency, notes):
        cursor = self.db.cursor()
        timestamp = time.time()
        cursor.execute("""INSERT INTO orders VALUES
                       (NULL, ?, ?, "SELL", ?, ?, ?, ?, ?, ?)""",
                       (timestamp, timestamp, nick, host, btcamount, price,
                        othercurrency, notes))
        self.db.commit()

    def refresh(self, host, id=None):
        results = self.get(host, id)
        if len(results) != 0:
            cursor = self.db.cursor()
            timestamp = time.time()
            for row in results:
                cursor.execute("""UPDATE orders SET refreshed_at=?
                               WHERE id=?""", (timestamp, row[0]))
            self.db.commit()
            return len(results)
        return False

    def remove(self, host, id=None):
        results = self.get(host, id)
        if len(results) != 0:
            cursor = self.db.cursor()
            for row in results:
                cursor.execute("""DELETE FROM orders where id=?""",
                               (row[0],))
            self.db.commit()
            return len(results)
        return False
    
def getAt(irc, msg, args, state):
    if args[0].lower() in ['at', '@']:
        args.pop(0)

def getBTC(irc, msg, args, state):
    if args[0].lower() in ['btc','bitcoin','bitcoins']:
        args.pop(0)

def getPositiveFloat(irc, msg, args, state, type='positive floating point number'):
    try:
        v = float(args[0])
        if v <= 0:
            raise ValueError, "only positive numbers allowed."
        state.args.append(v)
        del args[0]
    except ValueError:
        state.errorInvalid(type, args[0])

addConverter('at', getAt)
addConverter('positiveFloat', getPositiveFloat)
addConverter('btc', getBTC)

class OTCOrderBook(callbacks.Plugin):
    """This plugin maintains an order book for order entry over irc.
    Use commands 'buy' and 'sell' to enter orders.
    Use command 'renew' to renew your open orders.
    Use command 'remove' to cancel open orders.
    """
    threaded = True

    def __init__(self, irc):
        self.__parent = super(OTCOrderBook, self)
        self.__parent.__init__(irc)
        self.filename = conf.supybot.directories.data.dirize('OTCOrderBook.db')
        self.db = OTCOrderDB(self.filename)
        self.db.open()

    def die(self):
        self.__parent.die()
        self.db.close()

    def _checkHost(self, host):
        if self.registryValue('requireCloak'):
            if not "/" in host:
                return False
        return True

    def buy(self, irc, msg, args, btcamount, price, othercurrency, notes):
        """<btcamount> [btc|bitcoin|bitcoins] [at|@] <priceperbtc> <othercurrency> [<notes>]

        Logs a buy order for <btcamount> BTC, at a price of <priceperbtc>
        per BTC, in units of <othercurrency>. Use the optional <notes> field to
        put in any special notes.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        if not self._checkHost(msg.host):
            irc.error("For identification purposes, you must have a cloak "
                      "in order to use the order system.")
            return
        results = self.db.get(msg.host)
        if len(results) >= self.registryValue('maxUserOpenOrders'):
            irc.error("You may not have more than %s outstanding open orders." % \
                      self.registryValue('maxUserOpenOrders'))
            return

        self.db.buy(msg.nick, msg.host, btcamount, price, othercurrency.upper(), notes)
        irc.reply("Order entry successful. Use 'view' command to view your "
                  "open orders.")
    buy = wrap(buy, ['positiveFloat','btc','at','positiveFloat','something',
                     optional('text')])

    def sell(self, irc, msg, args, btcamount, price, othercurrency, notes):
        """<btcamount> [btc|bitcoin|bitcoins] [at|@] <priceperbtc> <othercurrency> [<notes>]

        Logs a sell order for <btcamount> BTC, at a price of <priceperbtc>
        per BTC, in units of <othercurrency>. Use the optional <notes> field to
        put in any special notes.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        if not self._checkHost(msg.host):
            irc.error("For identification purposes, you must have a cloak "
                      "in order to use the order system.")
            return
        results = self.db.get(msg.host)
        if len(results) >= self.registryValue('maxUserOpenOrders'):
            irc.error("You may not have more than %s outstanding open orders." % \
                      self.registryValue('maxUserOpenOrders'))
            return

        self.db.sell(msg.nick, msg.host, btcamount, price, othercurrency.upper(), notes)
        irc.reply("Order entry successful. Use 'view' command to view your "
                  "open orders.")
    sell = wrap(sell, ['positiveFloat','btc','at','positiveFloat','something',
                     optional('text')])

    def refresh(self, irc, msg, args, orderid):
        """[<orderid>]

        Refresh the timestamps on your outstanding orders. If optional
        <orderid> argument present, only refreshes that particular order.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        rv = self.db.refresh(msg.host, orderid)
        if rv is not False:
            irc.reply("Order refresh successful, %s orders refreshed." % rv)
        else:
            irc.error("No orders found to refresh. Try the 'view' command to"
                      "view your open orders.")
    refresh = wrap(refresh, [optional('int')])

    def remove(self, irc, msg, args, orderid):
        """[<orderid>]

        Remove your outstanding orders. If optional <orderid> argument present,
        only removes that particular order.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        rv = self.db.remove(msg.host, orderid)
        if rv is not False:
            irc.reply("Order remove successful, %s orders removed." % rv)
        else:
            irc.error("No orders found to remove. Try the 'view' command to"
                      "view your open orders.")
    remove = wrap(remove, [optional('int')])

    def view(self, irc, msg, args, orderid):
        """<orderid>

        View information about your outstanding orders. If optional <orderid>
        argument present, only show that particular order.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        results = self.db.get(msg.host, orderid)
        if len(results) == 0:
            irc.error("No orders found matching these criteria.")
            return
        L = ["%s %s %s %s BTC @ %s %s (%s)" % (time.ctime(refreshed_at),
                                          host,
                                          buysell,
                                          btcamount,
                                          price,
                                          othercurrency,
                                          notes) \
             for (id,
                  created_at,
                  refreshed_at,
                  buysell,
                  nick,
                  host,
                  btcamount,
                  price,
                  othercurrency,
                  notes) in results]

        irc.replies(L, joiner=" || ")
    view = wrap(view, [optional('int')])
    
    def book(self, irc, msg, args, currency):
        """<currency>

        Get a list of open orders in <currency>.
        """
        self.db.deleteExpired(self.registryValue('orderExpiry'))
        results = self.db.getCurrencyBook(currency)
        if len(results) == 0:
            irc.error("No orders for this currency present in database.")
            return
        if len(results) > self.registryValue('maxOrdersInBookList'):
            irc.error("Too many orders to list on channel. Visit the website "
                      "at http://bitcoin-otc.com/ to see the complete order "
                      "book in a nice table.")
            return
        L = ["%s %s@%s %s %s BTC @ %s %s (%s)" % (time.ctime(refreshed_at),
                                                  nick,
                                                  host,
                                                  buysell,
                                                  btcamount,
                                                  price,
                                                  othercurrency,
                                                  notes) \
             for (id,
                  created_at,
                  refreshed_at,
                  buysell,
                  nick,
                  host,
                  btcamount,
                  price,
                  othercurrency,
                  notes) in results]
        irc.replies(L, joiner=" || ")
    book = wrap(book, ['something'])

Class = OTCOrderBook


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
