import re
import json
import urllib2
import sqlite3

class ExchangeRates:
    def __init__(self, orderbook_db_path, json_path):
        self.json_path = json_path
        self.currency_rates = {}
        self.db = sqlite3.connect(orderbook_db_path)

    def _getCurrencyConversion(self, rawprice):
        conv = re.search(r'{(...) in (...)}', rawprice)
        if (conv is not None) and (conv.group(0).lower() not in self.currency_rates.keys()):
            googlerate = self._queryGoogleRate(conv.group(1), conv.group(2))
            self.currency_rates[conv.group(0).lower()] = googlerate

    def _queryGoogleRate(self, cur1, cur2):
        googlerate =urllib2.urlopen('http://www.google.com/ig/calculator?hl=en&q=1%s=?%s' % \
                (cur1, cur2,)).read()
        googlerate = re.sub(r'(\w+):', r'"\1":', googlerate) # badly formed json, missing quotes
        googlerate = json.loads(googlerate, parse_float=str, parse_int=str)
        if googlerate['error']:
            raise ValueError, googlerate['error']
        return googlerate['rhs'].split()[0]

    def write_json(self):
        f = open(self.json_path, 'w')
        f.write(json.dumps(self.currency_rates))
        f.close()

    def run(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT price FROM orders WHERE price LIKE ?""", ("%{___ in ___}%", ))
        result = cursor.fetchall()
        for item in result:
            self._getCurrencyConversion(item[0])
        self.write_json()

if __name__ == '__main__':
    er = ExchangeRates( 'otc/OTCOrderBook.db', 'exchangerates.json')
    er.run()