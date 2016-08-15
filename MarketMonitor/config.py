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
    conf.registerPlugin('MarketMonitor', True)

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

MarketMonitor = conf.registerPlugin('MarketMonitor')

conf.registerGlobalValue(MarketMonitor, 'channels',
    CommaSeparatedListOfChannels("", """List of channels that should
    receive monitoring output."""))
conf.registerGlobalValue(MarketMonitor, 'network',
    registry.String("freenode", """Network that should
    receive monitoring output."""))
conf.registerGlobalValue(MarketMonitor, 'autostart',
    registry.Boolean(False, """If true, will autostart monitoring upon bot
    startup."""))
conf.registerGlobalValue(MarketMonitor, 'marketsWhitelist',
    registry.SpaceSeparatedListOfStrings("", """Whitelist of markets you
    want to monitor, space separated list of short market names. Leave
    blank to include all."""))
conf.registerGlobalValue(MarketMonitor, 'marketsBlacklist',
    registry.SpaceSeparatedListOfStrings("", """Blacklist of markets you
    want to exclude, space separated list of short market names. Leave
    blank to include all."""))
conf.registerGlobalValue(MarketMonitor, 'collapseThreshold',
    registry.Integer(3, """Minimum number of transactions the bot will
    collapse together"""))
conf.registerGlobalValue(MarketMonitor, 'supportedMarkets',
    registry.SpaceSeparatedListOfStrings("Bitfinex Bitstamp", """List 
    of markets supported and enabled on this plugin."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
