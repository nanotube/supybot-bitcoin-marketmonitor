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
            yahoorate = self._queryYahooRate(conv.group(1), conv.group(2))
            self.currency_rates[conv.group(0).lower()] = yahoorate

    def _queryYahooRate(self, cur1, cur2):
        queryurl = "http://query.yahooapis.com/v1/public/yql?q=select%%20*%%20from%%20yahoo.finance.xchange%%20where%%20pair=%%22%s%s%%22&env=store://datatables.org/alltableswithkeys&format=json"
        yahoorate = urllib2.urlopen(queryurl % (cur1, cur2,)).read()
        yahoorate = json.loads(yahoorate, parse_float=str, parse_int=str)
        rate = yahoorate['query']['results']['rate']['Rate']
        if float(rate) == 0:
            raise ValueError, "no data"
        return rate

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