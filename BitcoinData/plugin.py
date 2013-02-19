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

def getHashrate(irc, msg, args, state, type='hashrate'):
    v = args[0].decode('utf8')
    siPfx = 'KMGTPEZY'
    tPfx = u'\u1d57\u02e2\u1d50\u1d47'
    m = re.match(r'([\d.]+)([' + siPfx + tPfx + '])?(h(?:[p/]?s)?)?', v, re.IGNORECASE)
    if not m:
        state.errorInvalid(type, args[0])
        return
    m = m.groups()
    v1 = float(m[0])
    if v1 <= 0:
        state.errorInvalid(type, args[0])
        return
    if m[1]:
        if m[1] in tPfx:
            v1 *= 0x10 ** (tPfx.find(m[1]) + 1)
        else:
            v1 *= 1e3 ** (siPfx.find(m[1].upper()) + 1)
    elif not m[2]:
        v1 *= 1e6
    state.args.append(v1)
    del args[0]
addConverter('hashrate', getHashrate)

class BitcoinData(callbacks.Plugin):
    """Includes a bunch of commands to retrieve or calculate various
    bits of data relating to bitcoin and the blockchain."""
    threaded = True

    def _grabapi(self, apipaths):
        sources = ['http://blockchain.info','http://blockexplorer.com', ]
        urls = [''.join(t) for t in zip(sources, apipaths)]
        for url in urls:
            try:
                data = urlopen(url, timeout=5).read()
                return data
            except:
                continue
        else:
            return None

    def avgprc(self, irc, msg, args, currency, timeframe):
        """<currency> <timeframe>

        Returns volume-weighted average price data from MtGox.
        <currency> is a three-letter currency code, <timeframe> is
        the time window for the average, and can be '24h', '7d', or '30d'.
        """
        try:
            data = urlopen('http://bitcoincharts.com/t/weighted_prices.json').read()
            j = json.loads(data)
            curs = j.keys()
            curs.remove('timestamp')
        except:
            irc.error("Failed to retrieve data. Try again later.")
            return
        try:
            result = j[currency.upper()][timeframe]
        except KeyError:
            irc.error("Data not available. Available currencies are %s, and "
                    "available timeframes are 24h, 7d, 30d." % (', '.join(curs),))
            return
        irc.reply(result)
    avgprc = wrap(avgprc, ['something','something'])

    def _blocks(self):
        data = self._grabapi(['/q/getblockcount']*2)
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
        
    def _rawblockbyhash(self, blockhash):
        data = self._grabapi(['/rawblock/%s' % blockhash]*2)
        return data
        
    def _rawblockbynum(self, blocknum):
        try:
            data = urlopen('http://blockexplorer.com/b/%s' % blocknum, timeout=5).read()
            m = re.search(r'href="(/rawblock/[0-9a-f]+)"', data)
            bbeurl = m.group(1)
        except:
            bbeurl = 'doesnotexist'
        data = self._grabapi(['/block-height/%s?format=json' % blocknum, bbeurl, ])
        try:
            j = json.loads(data)
            if 'blocks' in j.keys():
                j = j['blocks'][0]
            return j
        except:
            return None

    def _blockdiff(self, blocknum):
        block = self._rawblockbynum(blocknum)
        try:
            diffbits = block['bits']
            hexbits = hex(diffbits)
            target = int(hexbits[4:], 16) * 2 ** (8 * (int(hexbits[2:4], 16) - 3))
            maxtarget = float(0x00000000FFFF0000000000000000000000000000000000000000000000000000)
            diff = maxtarget / target
            return diff
        except:
            return None

    def blockdiff(self, irc, msg, args, blocknum):
        '''<block number>
        
        Get difficulty for specified <block number>.'''
        #data = self._grabapi(['b/%s' % blocknum, 'rawblock/%s' % blocknum])
        # first, let's try to grab from bbe, we need blockhash first
        diff = self._blockdiff(blocknum)
        if diff is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(diff)
    blockdiff = wrap(blockdiff, ['positiveInt'])

    def _diff(self):
        data = self._grabapi(['/q/getdifficulty']*2)
        return data

    def diff(self, irc, msg, args):
        '''takes no arguments
        
        Get current difficulty.'''
        data = self._diff()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    diff = wrap(diff)

    def _hextarget(self, blocknum):
        block = self._rawblockbynum(blocknum)
        try:
            diffbits = block['bits']
            hexbits = hex(diffbits)
            target = int(hexbits[4:], 16) * 2 ** (8 * (int(hexbits[2:4], 16) - 3))
            target = hex(target)[2:-1]
            target = '0'*(64-len(target)) + target
            return target.upper()
        except:
            return None

    def hextarget(self, irc, msg, args, blocknum):
        '''[<block number>]
        
        get the hex target for current block.
        if optional block number is provided, get hex target for that block height.
        '''
        if blocknum is None:
            blocknum = self._blocks()
        target = self._hextarget(blocknum)
        if target is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(target)
    hextarget = wrap(hextarget, [optional('positiveInt')])

    def _bounty(self):
        data = self._grabapi(['/q/bcperblock']*2)
        try:
            if int(data) > 50:
                return int(data) / 100000000
            else:
                return int(data)
        except:
            return None

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
        gentime = 2**48/65535*difficulty/hashrate
        return gentime

    def gentime(self, irc, msg, args, hashrate, difficulty):
        '''<hashrate> [<difficulty>]
        
        Calculate expected time to generate a block using <hashrate>,
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
        irc.reply("The average time to generate a block at %s h/s, given difficulty of %s, is %s" % \
                (hashrate, difficulty, utils.timeElapsed(gentime)))
    gentime = wrap(gentime, ['hashrate', optional('positiveFloat')])

    def genrate(self, irc, msg, args, hashrate, difficulty):
        '''<hashrate> [<difficulty>]
        
        Calculate expected bitcoin generation rate using <hashrate>,
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
        irc.reply("The expected generation output, at %s h/s, given difficulty of %s, is %s BTC "
                "per day and %s BTC per hour." % (hashrate, difficulty,
                            bounty*24*60*60/gentime,
                            bounty * 60*60/gentime))
    genrate = wrap(genrate, ['hashrate', optional('positiveFloat')])

    def tslb(self, irc, msg, args):
        """takes no arguments
        
        Shows time elapsed since latest generated block.
        This uses the block timestamp, so may be slightly off clock-time.
        """
        blocknum = self._blocks()
        block = self._rawblockbynum(blocknum)
        try:
            blocktime = block['time']
            irc.reply("Time since last block: %s" % utils.timeElapsed(time.time() - blocktime))
        except:
            irc.error("Problem retrieving latest block data.")
    tslb = wrap(tslb)
    
    def _nethash3d(self):
        try:
            estimate = urlopen('http://bitcoin.sipa.be/speed-3D.txt').read()
            estimate = float(estimate)
        except:
            estimate = None
        return estimate
    
    def _nethashsincelast(self):
        try:
            estimate = urlopen('http://blockexplorer.com/q/estimate').read()
            estimate = float(estimate) / 139.696254564
        except:
            estimate = None
        return estimate
    
    def nethash(self, irc, msg, args):
        '''takes no arguments
        
        Shows the current estimate for total network hash rate, in Ghps.
        '''
        data = self._nethash3d()
        if data is None:
            data = self._nethashsincelast()
        if data is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    nethash = wrap(nethash)

    def diffchange(self, irc, msg, args):
        """takes no arguments
        
        Shows estimated percent difficulty change.
        """
        currdiff = self._diff()
        try:
            diff3d = self._nethash3d() * 139.696254564
            diff3d = round(100*(diff3d/float(currdiff) - 1), 5)
        except:
            diff3d = None
        try:
            diffsincelast = self._nethashsincelast() * 139.696254564
            diffsincelast = round(100*(diffsincelast/float(currdiff) - 1), 5)
        except:
            diffsincelast = None
        irc.reply("Estimated percent change in difficulty this period | %s %% based on data since last change | %s %% based on data for last three days" % (diffsincelast, diff3d))
    diffchange = wrap(diffchange)
    
    def estimate(self, irc, msg, args):
        """takes no arguments
        
        Shows next difficulty estimate.
        """
        try:
            diff3d = self._nethash3d() * 139.696254564
        except:
            diff3d = None
        try:
            diffsincelast = self._nethashsincelast() * 139.696254564
        except:
            diffsincelast = None
        irc.reply("Next difficulty estimate | %s based on data since last change | %s based on data for last three days" % (diffsincelast, diff3d))
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

    def _nextretarget(self):
        data = self._grabapi(['/q/nextretarget']*2)
        return data
        
    def nextretarget(self, irc, msg, args):
        """takes no arguments
        
        Shows the block number at which the next difficulty change will take place.
        """
        data = self._nextretarget()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    nextretarget = wrap(nextretarget)

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

    def _interval(self):
        data = self._grabapi(['/q/interval']*2)
        return data
        
    def interval(self, irc, msg, args):
        """takes no arguments
        
        Shows average interval, in seconds, between last 1000 blocks.
        """
        data = self._interval()
        if data is None or data == '':
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply(data)
    interval = wrap(interval)

    def _timetonext(self):
        try:
            interval = float(self._interval())
            blocks = float(self._blocks())
            retarget = float(self._nextretarget())
            return (retarget - blocks)*interval
        except:
            return None

    def timetonext(self, irc, msg, args):
        """takes no arguments
        
        Show estimated time to next difficulty change.
        """
        data = self._timetonext()
        if data is None:
            irc.error("Failed to retrieve data. Try again later.")
            return
        irc.reply("%s" % data)
    timetonext = wrap(timetonext)

    def bcstats(self, irc, msg, args):
        """takes no arguments
        
        Shows a number of statistics about the state of the block chain.
        """
        blocks = self._blocks()
        diff = self._diff()
        try:
            estimate = self._nethashsincelast() * 139.696254564
        except:
            estimate = None
        try:
            diffchange = round((estimate/float(diff) - 1)  * 100, 5)
        except:
            diffchange = None
        nextretarget = self._nextretarget()
        try:
            blockstoretarget = int(nextretarget) - int(blocks)
        except:
            blockstoretarget = None
        try:
            timetonext = utils.timeElapsed(self._timetonext())
        except:
            timetonext = None        
        
        irc.reply("Current Blocks: %s | Current Difficulty: %s | "
                "Next Difficulty At Block: %s | "
                "Next Difficulty In: %s blocks | "
                "Next Difficulty In About: %s | "
                "Next Difficulty Estimate: %s | "
                "Estimated Percent Change: %s" % (blocks, diff, 
                        nextretarget, blockstoretarget, timetonext, 
                        estimate, diffchange))
    bcstats = wrap(bcstats)

#math calc 1-exp(-$1*1000 * [seconds $*] / (2**32* [bc,diff]))

    def _genprob(self, hashrate, interval, difficulty):
        genprob = 1-math.exp(-hashrate * interval / (2**32* difficulty))
        return genprob

    def genprob(self, irc, msg, args, hashrate, interval, difficulty):
        '''<hashrate> <interval> [<difficulty>]
        
        Calculate probability to generate a block using <hashrate>,
        in <interval> seconds, at current difficulty.
        If optional <difficulty> argument is provided, probability is for supplied difficulty.
        To provide the <interval> argument, a nested 'elapsed' command may be helpful.
        '''
        if difficulty is None:
            try:
                difficulty = float(self._diff())
            except:
                irc.error("Failed to current difficulty. Try again later or supply difficulty manually.")
                return
        gp = self._genprob(hashrate, interval, difficulty)
        irc.reply("The probability to generate a block at %s h/s within %s, given difficulty of %s, is %s" % \
                (hashrate, utils.timeElapsed(interval), difficulty, gp))
    genprob = wrap(genprob, ['hashrate', 'positiveInt', optional('positiveFloat')])


Class = BitcoinData


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
