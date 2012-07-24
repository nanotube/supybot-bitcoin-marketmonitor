#!/bin/bash
USER=${USER:-'anonymous'}
echo 'Paste your challenge string. Press ENTER'
read chal
sig=`echo $chal|gpg --clearsign`
if [ 0 -eq $? ]
then
	sig=`echo "$sig"|sed -e "s/\+/%2B/g"`
	echo "Your signature:
$sig"
	extra=`wget --post-data="poster=$USER&lang=text&expire=600&code=$sig" paste.debian.net  -q -O - |grep -m 1 -o 'paste.debian.net/plain/[0-9]*'` && echo "Your url is: http://${extra}" && exit 0
	echo 'ERROR: Pasting to paste.debian.net'
else
	echo 'ERROR: Signature failed.'
fi
exit 1
