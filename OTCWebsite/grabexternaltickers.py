###
# Retrieve ticker data from external sources and write in standardized format.
# Copyright (C) 2013, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
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

import urllib2
import json

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0')]
urllib2.install_opener(opener)

def get_bitstamp_ticker():
    try:
        json_data = urllib2.urlopen("https://www.bitstamp.net/api/ticker/").read()
        ticker = json.loads(json_data)
        bcharts = json.loads(urllib2.urlopen("http://api.bitcoincharts.com/v1/markets.json").read())
        bcharts = filter(lambda x: x['symbol'] == 'bitstampUSD', bcharts)[0]
        stdticker = {'bid': ticker['bid'],
                            'ask': ticker['ask'],
                            'last': ticker['last'],
                            'vol': ticker['volume'],
                            'low': ticker['low'],
                            'high': ticker['high'],
                            'avg': str(bcharts['avg'])}
    except:
        stdticker = {'error':'something failed'}
    return stdticker

def get_kraken_ticker():
    try:
        json_data = urllib2.urlopen("https://api.kraken.com/0/public/Ticker?pair=XBTUSD").read()
        ticker = json.loads(json_data)

        if ticker['error']:
            stdticker = {'error': "; ".join(ticker['error'])}
        else:
            tick = ticker['result']['XXBTZUSD']
            stdticker = {
                'bid': tick['b'][0],
                'ask': tick['a'][0],
                'last': tick['c'][0],
                'vol': tick['v'][0],
                'low': tick['l'][0],
                'high': tick['h'][0],
                'avg': tick['p'][0]
            }
    except:
        stdticker = {'error':'something failed'}
    return stdticker

def write_json(data, fname):
    f = open(fname, 'w')
    f.write(json.dumps(data))
    f.close()

if __name__ == '__main__':
    krktic = get_kraken_ticker()
    write_json(krktic, 'kraken.json')
    btsptic = get_bitstamp_ticker()
    write_json(btsptic, 'bitstamp.json')
