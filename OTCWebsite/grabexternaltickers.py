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

def get_mtgox_ticker():
    try:
        json_data = urllib2.urlopen("https://data.mtgox.com/api/2/BTC%s/money/ticker" % ('USD',)).read()
        ticker = json.loads(json_data)
        ftj = urllib2.urlopen("http://data.mtgox.com/api/2/BTC%s/money/ticker_fast" % ('USD',)).read()
        tf = json.loads(ftj)
        if ticker['result'] != 'error' and tf['result'] != 'error': # use fast ticker where available
            ticker['data']['buy']['value'] = tf['data']['buy']['value']
            ticker['data']['sell']['value'] = tf['data']['sell']['value']
            ticker['data']['last']['value'] = tf['data']['last']['value']
        if ticker['result'] == 'error':
             stdticker = {'error':ticker['error']}
        else:
            stdticker = {'bid': ticker['data']['buy']['value'],
                                'ask': ticker['data']['sell']['value'],
                                'last': ticker['data']['last']['value'],
                                'vol': ticker['data']['vol']['value'],
                                'low': ticker['data']['low']['value'],
                                'high': ticker['data']['high']['value'],
                                'avg': ticker['data']['vwap']['value']}
    except:
        stdticker = {'error':'something failed'}
    return stdticker

def write_json(data, fname):
    f = open(fname, 'w')
    f.write(json.dumps(data))
    f.close()

if __name__ == '__main__':
    goxtic = get_mtgox_ticker()
    write_json(goxtic, 'mtgox.json')
    btsptic = get_bitstamp_ticker()
    write_json(btsptic, 'bitstamp.json')
