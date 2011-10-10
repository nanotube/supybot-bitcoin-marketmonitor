/*
GPG authentication helper script for mIRC.

Version 2011.10.10.0000

Usage: /verify

You can install this script by typing /load -rs <path-to-script>

If you change the script, it should be re-initialized.

Inspiration/Original Source: joric/bitcoin-otc

Rewritten by: imsaguy/bitcoin-otc 
For tips: 1BonWMqpUChjFSdgY1qoAxzYLLnsYsFF79

TODO List:
**Better Error Checking
**Auth/Verify Support
**Registration

*/

on *:load:{
  unset %otcgpg*


  if ($isfile(C:\Program Files\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\gpg.exe"
    echo $color(info) -st * [OTCgpg]GPG Found At C:\Program Files\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\pub\gpg.exe"
    echo $color(info) -st * [OTCgpg]GPG Found At C:\Program Files\GNU\GnuPG\pub\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\gpg.exe"
    echo $color(info) -st * [OTCgpg]GPG Found At C:\Program Files (x86)\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe"
    echo $color(info) -st * [OTCgpg]GPG Found At C:\Program Files (x86)\GNU\GnuPG\pub
  }
  else {
    set %otcgpgpath $$?="I can't find GPG! Please make sure GPG is installed and enter the path to the directory in which otcgpgexe resides:"
    set %otcgpgpath chr(34) $+ %otcgpgpath $+ chr(34)
  }

  set %otcgpgbot $input(What is the name of the GPG bot?,e,GPG Bot name?,gribble)
  if (%otcgpgbot == $null) {
    set %otcgpgbot gribble
    echo $color(info) -st * [OTCgpg]Using default GPG bot name of gribble.
  } 

  while (%otcgpguser == $null) set %otcgpguser $input(What is your otc username?,eo,otc username)
  set %otcgpgpass $input(What is your gpg password?,po,gpg password)

  echo $color(info) -st * [OTCgpg]OTCgpg Helper script successfully setup.  Use /verify to ident to %otcgpgbot and gain voice in -otc.
}

alias verify {
  /msg %otcgpgbot ;;eauth %otcgpguser
}

alias otcgpg_decrypt {
  var %in = $scriptdir $+ $1
  var %out = $scriptdir $+ stdout.txt
  var %cmd = cmd /C echo %otcgpgpass $+ $chr(124) %otcgpgpath --batch --yes --passphrase-fd 0 --decrypt %in > %out
  /run -n %cmd
  .timer 1 10 /otcgpg_everify %out
}

alias otcgpg_everify {
  if ($isfile($1)) {
    .fopen f $1
    var %s = $fread(f)
    .fclose f
    /msg %otcgpgbot ;;everify %s
    .remove $1

  }
  else {
    .timer 1 10 otcgpg_everify $1
    echo $color(info) -st * [OTCgpg]Unable to decrypt the OTP. Did you type in your password?
  }
}

alias otcgpg_download {
  var %socket $+(otcdl,$chr(46),$nopath($1))
  if (!$sock(%socket)) {
    sockopen %socket $gettok($1,2,47) 80
    sockmark %socket HEAD $gettok($1,2,47) $+($chr(47),$gettok($1,3,47),$chr(47),$gettok($1,4,47))
    echo $color(info) -st * [OTCgpg]Beginning to get OTP.
  }
  else {
    echo $color(info) -st * [OTCgpg]Socket already in use.
  }
}

on *:SOCKOPEN:otcdl.*:{
  hadd -m ticks $sockname $ticks
  var %file = $nopath($gettok($sock($sockname).mark,3,32))
  var %fullfile = $+(",$scriptdir,%file,")
  var %sckr = sockwrite -n $sockname, %^ = $gettok($sock($sockname).mark,3,32)
  echo $color(info) -st * [OTCgpg]Connecting to OTP host...
  write -c %fullfile
  %sckr GET $iif(left(%^,1) != $chr(47),$chr(47) $+ %^,%^) HTTP/1.0
  %sckr HOST: $gettok($sock($sockname).mark,2,32)
  %sckr ACCEPT: *.*
  %sckr $crlf
}

on *:SOCKREAD:otcdl.*:{
  if ($sockerr) {
    echo $color(info) -st * [OTCgpg]Error: $sock($sockname).wsmsg
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
        ; When there are no vars, we now we have to start binary downloading
        echo $color(info) -st * [OTCgpg]Downloading %totsize bytes...
        sockmark $sockname GET $2- %totsize
      }
    }
    elseif ($1 == GET) {
      ; Downloading ...
      var %file = $+(",$scriptdir,$nopath($3),"), %cursize = $file(%file).size
      var %totsize = $gettok($sock($sockname).mark,4,32)
      bwrite %file -1 &b
    }
    goto begin
  }
}

on *:SOCKCLOSE:otcdl.*:{
  var %ticks = $calc(($ticks - $hget(ticks,$sockname)) /1000)
  var %filename = $nopath($gettok($sock($sockname).mark,3,32))
  echo $color(info) -st * [OTCgpg]File %filename downloaded in : %ticks seconds. Beginning decryption.
  /otcgpg_decrypt %filename
}

on *:TEXT:$(Request successful for user %otcgpguser $+ *):?: {
  if ($nick == %otcgpgbot) {
    /otcgpg_download $wildtok($1-, http://*, 1, 32)
  }
}

on *:TEXT:$(*You are now authenticated for user %otcgpguser $+ *):?: {
  if ($nick == %otcgpgbot) {
    /msg %otcgpgbot ;;voiceme
    echo $color(info) -st * [OTCgpg]Successfully authenticated to %otcgpgbot #+.
  }
}
