#/usr/bin/env python

#
# script to automatically gpg sign a message, upload it to paste.pocoo.org,
# and spit out the raw paste url. very effort-saving! 
#
# usage: 
# python gpgsigner.py yourchallengestringgoeshere
#

from xmlrpclib import ServerProxy
import subprocess
import sys
import StringIO

input = " ".join(sys.argv[1:])

p1 = subprocess.Popen(['gpg','--clearsign'], stdin = subprocess.PIPE, stdout=subprocess.PIPE)
p1.stdin.write(input)
output = p1.communicate()[0]

s = ServerProxy('http://paste.debian.net/server.pl')
rc = s.paste.addPaste(output, 'mygpgauth', 300)
pasteid = rc['id']
print "http://paste.debian.net/plain/%s/" % (pasteid,)