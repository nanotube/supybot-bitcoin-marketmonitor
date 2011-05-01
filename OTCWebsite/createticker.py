###
# Parse the OTC Order Book to create the inside quote ticker data.
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

import sqlite3
import urllib2
import re
import json
import os
import time

class Quote:
    def __init__(self, rawbids, rawasks, btcbidsinverse, btcasksinverse, currency, mtgox_ticker):
        self.currency = currency
        self.ticker = mtgox_ticker
        self.bids = []
        self.asks = []
        self.bestbid = None
        self.bestask = None
        self.currency_rates = {}
        for item in rawbids:
            bid = self._getIndexedValue(item[0])
            if bid is not None:
                self.bids.append(bid)
        for item in rawasks:
            ask = self._getIndexedValue(item[0])
            if ask is not None:
                self.asks.append(ask)
        for item in btcbidsinverse:
            bid = self._getIndexedValue(item[0], inverse=True)
            if bid is not None:
                self.bids.append(bid)
        for item in btcasksinverse:
            ask = self._getIndexedValue(item[0], inverse=True)
            if ask is not None:
                self.asks.append(ask)

        if len(self.bids) > 0:
            self.bestbid = max(self.bids)
        if len(self.asks) > 0:
            self.bestask = min(self.asks)

    def _getCurrencyConversion(self, rawprice):
        conv = re.search(r'{(...) in (...)}', rawprice)
        if conv is None:
            return rawprice
        if conv.group(0) not in self.currency_rates.keys():
            googlerate = self._queryGoogleRate(conv.group(1), conv.group(2))
            self.currency_rates[conv.group(0)] = googlerate
        indexedprice = re.sub(r'{... in ...}', self.currency_rates[conv.group(0)], rawprice)
        return indexedprice

    def _queryGoogleRate(self, cur1, cur2):
        googlerate =urllib2.urlopen('http://www.google.com/ig/calculator?hl=en&q=1%s=?%s' % \
                (cur1, cur2,)).read()
        googlerate = re.sub(r'(\w+):', r'"\1":', googlerate) # badly formed json, missing quotes
        googlerate = json.loads(googlerate, parse_float=str, parse_int=str)
        if googlerate['error']:
            raise ValueError, googlerate['error']
        return googlerate['rhs'].split()[0]

    def _getIndexedValue(self, rawprice, inverse=False):
        try:
            if self.ticker is not None:
                indexedprice = re.sub(r'{mtgoxask}', self.ticker['sell'], rawprice)
                indexedprice = re.sub(r'{mtgoxbid}', self.ticker['buy'], indexedprice)
                indexedprice = re.sub(r'{mtgoxlast}', self.ticker['last'], indexedprice)
            else:
                indexedprice = rawprice
            indexedprice = self._getCurrencyConversion(indexedprice)
            if inverse:
                indexedprice = 1. / indexedprice
            return "%.5g" % eval(indexedprice)
        except:
            return None

    def json(self):
        js = {self.currency: {'bid': self.bestbid, 'ask': self.bestask}}
        return js

    def sql(self):
        sql = "INSERT INTO quotes VALUES (NULL, '%s', '%s', '%s')" %\
                (self.currency, self.bestbid, self.bestask,)
        return sql

class QuoteCreator:
    def __init__(self, orderbook_db_path, quote_db_path, json_path):
        self.json_path = json_path
        self.quote_db_path = quote_db_path
        self.quotes = []
        self.currency_codes = \
            ['AED', 'ANG', 'ARS', 'AUD', 'BDT', 'BGN', 'BHD', 'BND', 'BOB',
            'BRL', 'BWP', 'CAD', 'CHF', 'CLP', 'CNY', 'COP', 'CRC', 'CZK',
            'DKK', 'DOP', 'DZD', 'EEK', 'EGP', 'EUR', 'FJD', 'GBP', 'HKD',
            'HNL', 'HRK', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'JMD', 'JOD',
            'JPY', 'KES', 'KRW', 'KWD', 'KYD', 'KZT', 'LBP', 'LKR', 'LTL',
            'LVL', 'MAD', 'MDL', 'MKD', 'MUR', 'MVR', 'MXN', 'MYR', 'NAD',
            'NGN', 'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PEN', 'PGK', 'PHP',
            'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'SAR', 'SCR',
            'SEK', 'SGD', 'SKK', 'SLL', 'SVC', 'THB', 'TND', 'TRY', 'TTD',
            'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS', 'VEF', 'VND',
            'XOF', 'YER', 'ZAR', 'ZMK', 'ZWR',]
        self.db1 = sqlite3.connect(orderbook_db_path)

    def run(self):
        try:
            self.get_mtgox_quote()
        except:
            self.mtgox_ticker = None
        self.create_quotes()
        self.write_quotedb()
        self.write_json()

    def get_mtgox_quote(self):
        mtgox_ticker = urllib2.urlopen('http://mtgox.com/code/ticker.php').read()
        self.mtgox_ticker = json.loads(mtgox_ticker, parse_float=str, parse_int=str)
        self.mtgox_ticker = self.mtgox_ticker['ticker']

    def create_quotes(self):
        cursor = self.db1.cursor()
        for code in self.currency_codes:
            sql = """SELECT price FROM orders WHERE
                    (buysell = 'BUY' AND thing LIKE 'BTC' AND otherthing LIKE ?)"""
            cursor.execute(sql, (code,))
            btcbids = cursor.fetchall()
            sql = """SELECT price FROM orders WHERE
                    (buysell = 'SELL' AND thing LIKE ? AND otherthing LIKE 'BTC')"""
            cursor.execute(sql, (code,))
            btcbidsinverse = cursor.fetchall()

            sql = """SELECT price FROM orders WHERE
                    (buysell = 'SELL' AND thing LIKE 'BTC' AND otherthing LIKE ?)"""
            cursor.execute(sql, (code,))
            btcasks = cursor.fetchall()
            sql = """SELECT price FROM orders WHERE
                    (buysell = 'BUY' AND thing LIKE ? AND otherthing LIKE 'BTC')"""
            cursor.execute(sql, (code,))
            btcasksinverse = cursor.fetchall()

            if len(btcasks) != 0 or len(btcbids) != 0:
                quote = Quote(btcbids, btcasks, btcbidsinverse, btcasksinverse, code, self.mtgox_ticker)
                self.quotes.append(quote)

    def write_quotedb(self):
        try:
            os.remove(self.quote_db_path)
        except OSError:
            pass
        db2 = sqlite3.connect(self.quote_db_path)
        cursor = db2.cursor()
        cursor.execute("""CREATE TABLE quotes (
                          id INTEGER PRIMARY KEY,
                          currency TEXT,
                          bid TEXT,
                          ask TEXT)
                          """)
        db2.commit()
        for quote in self.quotes:
            cursor.execute(quote.sql())
        db2.commit()

    def write_json(self):
        json_dict = {}
        [json_dict.update(quote.json()) for quote in self.quotes]
        json_dict = {'ticker': json_dict, 'timestamp': time.time()}
        f = open(self.json_path, 'w')
        f.write(json.dumps(json_dict))
        f.close()

if __name__ == '__main__':
    qc = QuoteCreator('otc/OTCOrderBook.db', 'OTCQuotes.db', 'quotes.json')
    qc.run()
