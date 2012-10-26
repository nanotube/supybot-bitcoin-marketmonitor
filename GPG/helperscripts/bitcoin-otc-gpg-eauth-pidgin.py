#!/usr/bin/env python

#
# Azelphur's quick and ugly Bitcoin-OTC Pidgin auto auth script
# Usage: run the script, enter your GPG password, type ;;eauth YourNick, be happy.
# License: GPL
#
# You must also have the python-gnupg module.
# Get it from http://code.google.com/p/python-gnupg/

VOICEME = True # You can change this if you like

import dbus
import gobject
import re
import urllib2
import gnupg
import sys
from getpass import getpass
from dbus.mainloop.glib import DBusGMainLoop

class PidginOTC:
    def __init__(self):
        self.msg = re.compile('^Request successful for user .+?, hostmask .+. Get your encrypted OTP from (http:\/\/bitcoin-otc.com\/otps\/.+)$')
        self.gpg = gnupg.GPG()
        self.passphrase = getpass("Enter your GPG passphrase: ")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
        self.purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

        bus.add_signal_receiver(self.ReceivedImMsg,
                                dbus_interface="im.pidgin.purple.PurpleInterface",
                                signal_name="ReceivedImMsg")

        loop = gobject.MainLoop()

        loop.run()

    def ReceivedImMsg(self, account, sender, message, conversation, flags):
        if sender == 'gribble':
            match = self.msg.match(message) 
            if match:
                print 'recieved request from gribble, grabbing', match.group(1)
                data = urllib2.urlopen(match.group(1)).read()
                decrypted = str(self.gpg.decrypt(data, passphrase=self.passphrase))
                m = re.search("freenode:#bitcoin-otc:[a-f0-9]{56}", decrypted)
                if m is not None:
                    reply = ";;gpg everify "+m.group(0)
                    print 'replying with', reply
                    self.purple.PurpleConvImSend(self.purple.PurpleConvIm(conversation), reply)
                    if VOICEME:
                        self.purple.PurpleConvImSend(self.purple.PurpleConvIm(conversation), ";;voiceme")
                else:
                    print 'Error: Decrypted message does not contain expected challenge string format.'

PidginOTC()