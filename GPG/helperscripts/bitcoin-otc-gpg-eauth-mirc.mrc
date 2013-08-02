/*
GPG authentication helper script for mIRC.
Version 2013.08.02.00000

Usage: /verify PASSWORD

You can install this script by typing /load -rs <path-to-script>

If you change the script, it should be re-initialized.

Original Source: joric/bitcoin-otc
Rewritten by: imsaguy/bitcoin-otc

Slowness of authentication fixed by Happzz (markus/bitcoin-otc)
Tips to 1QKB2kDVtYwWdYCzKdchbuvkzYc2t38xGU
*/

on *:load:{
  window -e @otcgpg
  unset %otcgpg*

  if ($isfile(C:\Program Files\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\gpg.exe"
    echo @otcgpg GPG Found At C:\Program Files\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\pub\gpg.exe"
    echo @otcgpg GPG Found At C:\Program Files\GNU\GnuPG\pub\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\gpg.exe"
    echo @otcgpg GPG Found At C:\Program Files (x86)\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe"
    echo @otcgpg GPG Found At C:\Program Files (x86)\GNU\GnuPG\pub
  }
  else {
    set %otcgpgpath $$?="I can't find GPG! Please make sure GPG is installed and enter the path to the directory in which otcgpgexe resides:"
    set %otcgpgpath chr(34) $+ %otcgpgpath $+ chr(34)
  }
  set %otcgpgbot $input(What is the name of the GPG bot?,e,GPG Bot name?,gribble)
  if (%otcgpgbot == $null) {
    set %otcgpgbot gribble
    echo @otcgpg Using default GPG bot name of gribble.
  } 
  while (%otcgpguser == $null) set %otcgpguser $input(What is your otc username?,eo,otc username)
  echo @otcgpg OTCgpg Helper script successfully setup.  Use /verify password to ident to %otcgpgbot and gain voice in -otc.
}

alias verify {
  window -e @otcgpg
  echo @otcgpg [>] Slowness of authentication fixed by Happzz (markus/bitcoin-otc). Tips to 1QKB2kDVtYwWdYCzKdchbuvkzYc2t38xGU :)
  msg %otcgpgbot ;;eauth %otcgpguser
  set %otcgpgpass $1
}

on *:TEXT:$(Request successful for user %otcgpguser $+ *):?: {
  if ($nick == %otcgpgbot) {
    echo @otcgpg [*] Got URL from $+($chr(2),%otcgpgbot,$chr(2),:) $wildtok($1-, http://*, 1, 32)
    var %wildtok = $wildtok($1-, http://*, 1, 32)
    var %socket $+(otcdl,$chr(46),$nopath(%wildtok))
    if ($sock(%socket)) { sockclose %socket }
    echo @otcgpg [*] Fetching %wildtok
    sockopen %socket $gettok(%wildtok,2,47) 80
    sockmark %socket HEAD $gettok(%wildtok,2,47) $+($chr(47),$gettok(%wildtok,3,47),$chr(47),$gettok(%wildtok,4,47))
    var %ticks = $ticks
  }
}

on *:SOCKOPEN:otcdl.*:{
  write -c $qt($scriptdir $+ $nopath($gettok($sock($sockname).mark,3,32)))
  var %sckr = sockwrite -n $sockname, %^ = $gettok($sock($sockname).mark,3,32)
  %sckr GET %^ HTTP/1.1
  %sckr HOST: $gettok($sock($sockname).mark,2,32)
  %sckr ACCEPT: *.*
  %sckr $crlf
}

on *:SOCKREAD:otcdl.*:{
  if ($sockerr) {
    echo @otcgpg Error: $sock($sockname).wsmsg
    return
  }
  var %a
  :begin
  if ($gettok($sock($sockname).mark,1,32) == head) {
    sockread %a
  }
  else {
    sockread &b
  }
  if ($sockbr) {
    tokenize 32 $sock($sockname).mark
    if ($1 == HEAD) {
      if (%a) {
        ; Catching the file size, avoiding the data header
        if ($gettok(%a,1,32) == Content-Length:) { var %totsize = $gettok(%a,2,32) }
      }
      else {
        ; When there are no vars, we have to start a binary download
        sockmark $sockname GET $2- %totsize
      }
    }
    elseif ($1 == GET) {
      ; Downloading ...
      var %file = $+(",$scriptdir,$nopath($3),")
      bwrite %file -1 &b
      var %file = $qt($scriptdir $+ $nopath($gettok($sock($sockname).mark,3,32)))
      echo @otcgpg [*] Downloaded $file(%file).size bytes to %file

    }
    goto begin
  }
  else {
    var %filename = $nopath($gettok($sock($sockname).mark,3,32))
    var %in = $scriptdir $+ %filename
    var %out = $scriptdir $+ stdout.txt
    run -n cmd.exe /C echo %otcgpgpass $+ $chr(124) %otcgpgpath --batch --yes --passphrase-fd 0 --decrypt %in > %out
    unset %otcgpgpass
    sockclose $sockname
    timer 1 1 otcgpg_everify %out %in
  }
}

alias otcgpg_everify {
  if ($isfile($1)) {
    .fopen f $1
    var %s = $fread(f)
    .fclose f
    echo @otcgpg [*] DECRYPTED: %s
    msg %otcgpgbot ;;everify %s
    .timer 1 3 .remove $1 $2
    .unset %s
  }
  else {
    echo @otcgpg Unable to decrypt the OTP. Did you type in your password?
  }
}

on *:TEXT:$(*You are now authenticated for user %otcgpguser $+ *):?: {
  if ($nick == %otcgpgbot) {
    msg %otcgpgbot ;;voiceme
    echo @otcgpg [*] Successfully authenticated to %otcgpgbot
  }
}
