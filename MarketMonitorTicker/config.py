import supybot.conf as conf
import supybot.registry as registry
from supybot import ircutils
import re

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('MarketMonitorTicker', True)

class Channel(registry.String):
    def setValue(self, v):
        if not ircutils.isChannel(v):
            self.error()
        else:
            super(Channel, self).setValue(v)

class CommaSeparatedListOfChannels(registry.SeparatedListOf):
    Value = Channel
    def splitter(self, s):
        return re.split(r'\s*,\s*', s)
    joiner = ', '.join

MarketMonitorTicker = conf.registerPlugin('MarketMonitorTicker')

conf.registerGlobalValue(MarketMonitorTicker, 'channels',
    CommaSeparatedListOfChannels("", """List of channels that should
    receive monitoring output."""))
conf.registerGlobalValue(MarketMonitorTicker, 'network',
    registry.String("freenode", """Network that should
    receive monitoring output."""))
conf.registerGlobalValue(MarketMonitorTicker, 'tickerUrl',
    registry.String("https://mtgox.com/code/ticker.php", """Url with 
    the ticker data."""))
conf.registerGlobalValue(MarketMonitorTicker, 'autostart',
    registry.Boolean(False, """If true, will autostart monitoring upon bot
    startup."""))
conf.registerGlobalValue(MarketMonitorTicker, 'pollInterval',
    registry.PositiveInteger(30, """Poll interval, in seconds."""))

#conf.registerGlobalValue(MarketMonitorTicker, 'colors',
#    registry.Boolean(False, """If true, upticks will be green and downticks
#    will be red."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
