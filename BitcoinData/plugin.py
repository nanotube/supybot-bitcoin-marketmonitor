###
# Copyright (c) 2012, Daniel Folkinshteyn
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

from urllib2 import urlopen
import json
import re
import time
import math
import urllib2
import decimal
from StringIO import StringIO
import gzip
import traceback

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0')]
urllib2.install_opener(opener)

def getPositiveFloat(irc, msg, args, state, type='positiveFloat'):
    v = args[0]
    try:
        v1 = float(v)
        if v1 <= 0:
            state.errorInvalid(type, args[0])
            return
    except:
        state.errorInvalid(type, args[0])
        return
    state.args.append(v1)
    del args[0]
    
addConverter('positiveFloat', getPositiveFloat)

class BitcoinData(callbacks.Plugin):
    """Includes a bunch of commands to retrieve or calculate various
    bits of data relating to bitcoin and the blockchain."""
    threaded = True

    def _grabapi(self, apipaths):
        sources = ['https://blockstream.info', ]
        urls = [''.join(t) for t in zip(sources, apipaths)]
        for url in urls:
            try:
                req = urllib2.Request(url, headers={'User-Agent' : "I am a Browser"})
                response = urlopen(req, timeout=5)
                # some caches ignore Accept-Encoding and send us gzip anyway
                if response.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(response.read())
                    f = gzip.GzipFile(fileobj=buf)
                    data = f.read()
                else:
                    data = response.read()
                if "endpoint does not exist" not in data:
                    return data
            except Exception, e:
                traceback.print_exc()
                continue
        else:
            return None

    def _netinfo(self):
        try:
            data = urllib2.urlopen('https://api.blockchair.com/bitcoin/stats').read()
            data = json.loads(data)
            return data['data']
        except:
            return None

    def _blocks24h(self):
        data = self._netinfo()['blocks_24h']
        return data

    def _blocks(self):
        data = self._grabapi(['/api/blocks/tip/height'])
        return data

    def _diff(self):
        data = self._netinfo()['difficulty']
        return data

    def blocks(self, irc, msg, args):
        '''takes no arguments
        
        Get current block count.'''
        data = self._blocks()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    blocks = wrap(blocks)

    def _fees(self):
        data = self._grabapi(['/api/fee-estimates'])
        return data

    def fees(self, irc, msg, args):
        '''takes no arguments
        
        Get current fee estimates, in satoshis per byte, for desired
        confirmation within 2,4,6,10,20, and 144 blocks.
        Data from blockstream.info api. May be overly generous.
        Double check by reviewing the mempool.'''
        data = self._fees()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        try:
            data = json.loads(data)
            irc.reply("Fee estimates (blocks: fee): (2: %s),"
                "(4: %s), (6: %s), (10: %s), (20: %s), (144: %s)" % \
                (data.get('2','na'), data.get('4', 'na'), data.get('6','na'),
                data.get('10','na'), data.get('20','na'), data.get('144', 'na')))
        except:
            irc.error('Data error. Try again later.')
    fees = wrap(fees)

    def _mempool(self):
        #data1 = self._grabapi(['/api/mempool'])
        try:
            data1 = urllib2.urlopen('https://mempool.space/api/mempool').read()
        except:
            data1 = None
        try:
            data2 = urllib2.urlopen('https://mempool.space/api/v1/fees/mempool-blocks').read()
        except:
            data2 = None
        return (data1, data2)

    def mempool(self, irc, msg, args):
        '''takes no arguments
        
        Get current state of mempool. Includes total tx count, 
        total size in vbytes, total fees in satoshis, and a fee
        histogram, at breakpoints of 5,10,50,100,200,500 sats per
        vbyte.'''
        info = self._mempool()
        mempoolinfo = nextblock = nextblock1 = nextblock2 = 'na'
        try:
            data = json.loads(info[0])
            txcount = data['count']
            vsize = float(data['vsize'])/1048576
            totalfee = float(data['total_fee'])/1e8
            mempoolinfo = "[txcount: %s, vsize (MB): %s, totalfee (BTC): %s]" % \
                (txcount, vsize, totalfee)
        except:
            pass
        try:
            data = json.loads(info[1])
            nextblock = "[max fee: %s, min fee: %s]" % \
                (max(data[0]['feeRange']), min(data[0]['feeRange']))
            nextblock1 = "[max fee: %s, min fee: %s]" % \
                (max(data[1]['feeRange']), min(data[1]['feeRange']))
            nextblock2 = "[max fee: %s, min fee: %s]" % \
                (max(data[2]['feeRange']), min(data[2]['feeRange']))
        except:
            pass

        irc.reply("Mempool info: %s | Next block 0: %s | Next block 1: %s"
                " | Next block 2: %s" % \
            (mempoolinfo, nextblock, nextblock1, nextblock2))
    mempool = wrap(mempool)

    def _getrawblock(self, blockid):
        # either height or hash
        if str(blockid)[0:2] != '00': # then not a hash of block
            try:
                blockid = int(blockid)
                bh = self._blockhash(blockid)
            except ValueError:
                irc.error("Invalid hash or block number.")
                return
        else:
            bh = blockid
        
        data = self._grabapi(['/api/block/%s' % bh])
        data = json.loads(data)
        return data
    
    def _blockhash(self, height):
        data = self._grabapi(['/api/block-height/%s' % height])
        return data
        
    def _blockdiff(self, blockid):
        block = self._getrawblock(blockid)
        bits = block['bits']
        bits = hex(bits)[2:]
        target = int(bits[2:], base=16) * 2**(8* (int(bits[0:2], base=16)-3))
        difficulty = float(0xffff0000000000000000000000000000000000000000000000000000 / target)
        return difficulty

    def blockdiff(self, irc, msg, args, blocknum):
        '''<block number | block hash>
        
        Get difficulty for specified <block number> or <block hash>.'''
        diff = self._blockdiff(blocknum)
        if diff is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(diff)
    blockdiff = wrap(blockdiff, ['something'])

    def diff(self, irc, msg, args):
        '''takes no arguments
        
        Get current difficulty.'''
        data = self._diff()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    diff = wrap(diff)

    def _bounty(self):
        blocks = int(self._blocks())
        retargets = int(blocks/210000)
        bounty = 50.0 / 2**retargets
        return bounty
        
    def bounty(self, irc, msg, args):
        '''takes no arguments
        
        Get current block bounty.'''
        data = self._bounty()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    bounty = wrap(bounty)

    def _gentime(self, hashrate, difficulty):
        gentime = 2**48/65535*difficulty/hashrate/1000000000000
        return gentime

    def gentime(self, irc, msg, args, hashrate, difficulty):
        '''<hashrate> [<difficulty>]
        
        Calculate expected time to generate a block using <hashrate> Thps,
        at current difficulty. If optional <difficulty> argument is provided, expected
        generation time is for supplied difficulty.
        '''
        if difficulty is None:
            try:
                difficulty = float(self._diff())
            except:
                irc.error("Failed to fetch current difficulty. Try again later or supply difficulty manually.")
                return
        gentime = self._gentime(hashrate, difficulty)
        irc.reply("The average time to generate a block at %s Thps, given difficulty of %s, is %s" % \
                (hashrate, difficulty, utils.timeElapsed(gentime)))
    gentime = wrap(gentime, ['positiveFloat', optional('positiveFloat')])

    def genrate(self, irc, msg, args, hashrate, difficulty):
        '''<hashrate> [<difficulty>]
        
        Calculate expected bitcoin generation rate using <hashrate> Thps,
        at current difficulty. If optional <difficulty> argument is provided, expected
        generation time is for supplied difficulty.
        '''
        if difficulty is None:
            try:
                difficulty = float(self._diff())
            except:
                irc.error("Failed to retrieve current difficulty. Try again later or supply difficulty manually.")
                return
        gentime = self._gentime(hashrate, difficulty)
        try:
            bounty = float(self._bounty())
        except:
            irc.error("Failed to retrieve current block bounty. Try again later.")
            return
        irc.reply("The expected generation output, at %s Thps, given difficulty of %s, is %s BTC "
                "per day and %s BTC per hour." % (hashrate, difficulty,
                            bounty*24*60*60/gentime,
                            bounty * 60*60/gentime))
    genrate = wrap(genrate, ['positiveFloat', optional('positiveFloat')])

    def tslb(self, irc, msg, args):
        """takes no arguments
        
        Shows time elapsed since latest generated block.
        This uses the block timestamp, so may be slightly off clock-time.
        """
        blocknum = self._blocks()
        block = self._getrawblock(blocknum)
        try:
            blocktime = block['timestamp']
            irc.reply("Time since last block: %s" % utils.timeElapsed(time.time() - blocktime))
        except:
            irc.error("Problem retrieving latest block data.")
    tslb = wrap(tslb)

    def nethash(self, irc, msg, args):
        '''takes no arguments
        
        Shows the current estimate for total network hash rate, in Thps.
        '''
        data = self._netinfo()['hashrate_24h']
        if data is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(float(data)/1000000000000)
    nethash = wrap(nethash)

    def diffchange(self, irc, msg, args):
        """takes no arguments
        
        Shows estimated percent difficulty change.
        """
        blocks24h = self._blocks24h()
        try:
            change = round((float(blocks24h)/144-1)*100, 5)
        except:
            change = None
        irc.reply("Estimated percent change in difficulty this period %s %% given that %d blocks were found in the last 24h" % (change,blocks24h))
    diffchange = wrap(diffchange)
    
    def estimate(self, irc, msg, args):
        """takes no arguments
        
        Shows next difficulty estimate.
        """
        try:
            diff = self._diff()
            blocks24h = self._blocks24h()
            est = decimal.Decimal(float(diff)*float(blocks24h)/144)
        except:
            est = None
        irc.reply("Next difficulty estimate %s based on data for last 24h" % (est,))
    estimate = wrap(estimate)

    def totalbc(self, irc, msg, args):
        """takes no arguments
        
        Return total number of bitcoins created thus far.
        """
        try:
            blocks = int(self._blocks()) + 1 # offset for block0
        except:
            irc.error("Failed to retrieve block count. Try again later.")
            return
        bounty = 50.
        chunk = 210000
        total = 0.
        while blocks > chunk:
            total += chunk * bounty
            blocks -= 210000
            bounty /= 2.
        if blocks > 0:
            total += blocks * bounty
        irc.reply("%s" % total)
    totalbc = wrap(totalbc)

    def halfreward(self, irc, msg, args):
        """takes no arguments
        
        Show estimated time of next block bounty halving.
        """
        try:
            blocks = int(self._blocks())
        except:
            irc.error("Failed to retrieve block count. Try again later.")
            return
        halfpoint = 210000
        while halfpoint < blocks:
            halfpoint += 210000
        blocksremaining = halfpoint - blocks
        sectohalve = blocksremaining * 10 * 60
        irc.reply("Estimated time of bitcoin block reward halving: %s UTC | Time remaining: %s." % \
                (time.asctime(time.gmtime(time.time() + sectohalve)), utils.timeElapsed(sectohalve)))
    halfreward = wrap(halfreward)

    def _prevdiff(self):
        blocks = int(self._blocks())
        prevdiff = self._blockdiff(blocks - 2016)
        return prevdiff
        
    def prevdiff(self, irc, msg, args):
        """takes no arguments
        
        Shows the previous difficulty level.
        """
        data = self._prevdiff()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    prevdiff = wrap(prevdiff)
    
    def prevdiffchange(self, irc, msg, args):
        """takes no arguments
        
        Shows the percentage change from previous to current difficulty level.
        """
        try:
            prevdiff = float(self._prevdiff())
            diff = float(self._diff())
        except:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply("%s" % (round((diff / prevdiff - 1) * 100, 5), ))
    prevdiffchange = wrap(prevdiffchange)

#math calc 1-exp(-$1*1000 * [seconds $*] / (2**32* [bc,diff]))

    def _genprob(self, hashrate, interval, difficulty):
        genprob = 1-math.exp(-hashrate*1000000000000 * interval / (2**32* difficulty))
        return genprob

    def genprob(self, irc, msg, args, hashrate, interval, difficulty):
        '''<hashrate> <interval> [<difficulty>]
        
        Calculate probability to generate a block using <hashrate> Thps,
        in <interval> seconds, at current difficulty.
        If optional <difficulty> argument is provided, probability is for supplied difficulty.
        To provide the <interval> argument, a nested 'seconds' command may be helpful.
        '''
        if difficulty is None:
            try:
                difficulty = float(self._diff())
            except:
                irc.error("Failed to current difficulty. Try again later or supply difficulty manually.")
                return
        gp = self._genprob(hashrate, interval, difficulty)
        irc.reply("The probability to generate a block at %s Thps within %s, given difficulty of %s, is %s" % \
                (hashrate, utils.timeElapsed(interval), difficulty, gp))
    genprob = wrap(genprob, ['positiveFloat', 'positiveInt', optional('positiveFloat')])

    def tblb(self, irc, msg, args, interval):
        """<interval>
        
        Calculate the expected time between blocks which take at least
        <interval> seconds to create.
        To provide the <interval> argument, a nested 'seconds' command may be helpful.
        """
        try:
            difficulty = float(self._diff())
            nh = float(self._netinfo()['hashrate_24h'])/1e12
            gp = self._genprob(nh, interval, difficulty)
        except:
            irc.error("Problem retrieving data. Try again later.")
            return
        sblb = (difficulty * 2**48 / 65535) / (nh * 1e12) / (1 - gp)
        irc.reply("The expected time between blocks taking %s to generate is %s" % \
                (utils.timeElapsed(interval), utils.timeElapsed(sblb),))
    tblb = wrap(tblb, ['positiveInt'])


Class = BitcoinData


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
