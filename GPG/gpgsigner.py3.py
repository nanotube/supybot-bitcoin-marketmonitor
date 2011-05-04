#/usr/bin/env python

#
# script to automatically gpg sign a message, upload it to paste.pocoo.org,
# and spit out the raw paste url. very effort-saving! 
#
# usage: 
# python gpgsigner.py yourchallengestringgoeshere
#
# original code by nanotube, python 3 port by PLATO

from xmlrpc.client import ServerProxy
import subprocess
import sys
import io

input = " ".join(sys.argv[1:])

p1 = subprocess.Popen(['gpg','--clearsign'], stdin = subprocess.PIPE, stdout=subprocess.PIPE)
p1.stdin.write(bytes(input, 'UTF8'))
output = p1.communicate()[0]

s = ServerProxy('http://paste.pocoo.org/xmlrpc/')
pasteid = s.pastes.newPaste('text',output.decode())
print ("http://paste.pocoo.org/raw/",pasteid,"/", sep="")
