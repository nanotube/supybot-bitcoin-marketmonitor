# Supybot Bitcoin Market Monitor
A webapp and set of plugins for supybot that power a rich alternative currency monitoring and trading system over
 a chat network.

## Development Environment Setup
1. Install GnuPG.
2. Create a Python environment or virtualenv and activate it.
3. In that environment:

        pip install ecdsa # For the GPG plugin
        pip install lxml # For the GPGExt plugin

4. Download gribble source code:

        git clone git://git.code.sf.net/p/gribble/code gribble-code

5. Install it in your Python environment:

        cd gribble-code
        python setup.py install

6. Create a directory to be the bot's home and `cd` to it.
7. Run `supybot-wizard` to create the bot's directory structure and initial configuration.
  * Some plugins expect the bot to be present in #bitcoin-otc, #bitcoin-otc-auth, and #bitcoin-otc-ticker

8. Symlink or copy desired supybot-bitcoin-marketmonitor's directories over to the bot's new plugins directory.

9. Launch the bot:

        supybot gribble.conf  # Or whatever you've named its configuration file

10. On IRC, identify with the bot using the owner login name and password you set up during `supybot-wizard`.

11. On IRC, use supybot's `load` command to load desired plugins.
 * `OTCWebsite` is not a plugin, so don't worry about that one.

For more details on supybot installation, see http://sourceforge.net/apps/mediawiki/gribble/index.php?title=Supybot_Install_Guide

## Testing
1. create an empty directory to be used as your test environment, and `cd` to it.
2. `supybot-test path/to/your/plugins/PluginName` for whatever plugin you wish to run the tests for.