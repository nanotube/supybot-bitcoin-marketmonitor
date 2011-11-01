/*
OTCgpg helper script for #bitcoin-otc .01 
originally by imsaguy et al.
modified and improved by +ageis

to install, type /load -rs <script_filename.mrc>

new features:
popup menus for channel & userlist
settings/configuration
two options for downloading OTP
ASCII-encrypted passwords
automatic verify on join

todo:
gpg registration
buy/sell system
*/

menu Nicklist {
  OTCgpg
  .Ident:msg %otcgpgbot ;;ident $1
  .GPG info:msg %otcgpgbot ;;gpg info $1
  .Get trust:msg %otcgpgbot ;;gettrust $1
  .Rate
  ..Rate:msg %otcgpgbot ;;rate $1 $$?="Enter a rating (-10 to 10):" $$?="Comments:"
  ..Unrate:msg %otcgpgbot ;;unrate $1 
  ..Rated?:msg %otcgpgbot ;;rated $1
  ..Get rating:msg %otcgpgbot ;;getrating $1
  .Tell
  ..Now:msg %otcgpgbot ;;tell $1 $$?="What's your message?"
  ..Later:msg %otcgpgbot ;;later tell $1 $$?="What's your message?"
  ..Offer guide:msg %otcgpgchan ;;tell $1 [guide]
  ..GPG instructions:msg %otcgpgchan ;;tell $1 [gpg]
  .WoT
  ..Ratings received
  ...All:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=ANY&type=RECV
    echo $color(info) -st * [OTCgpg] Looking up all ratings received for $1 . . .
  }
  ...Positive:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=POS&type=RECV
    echo $color(info) -st * [OTCgpg] Looking up all positive ratings received for $1 . . .    
  }
  ...Negative:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=NEG&type=RECV 
    echo $color(info) -st * [OTCgpg] Looking up all negative ratings received for $1 . . .
  }
  ..Ratings sent
  ...All:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=ANY&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all ratings sent by $1 . . .
  }
  ...Positive:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=POS&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all positive ratings sent by $1 . . .
  }
  ...Negative:{
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ $1 $+ &sign=NEG&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all negative ratings sent by $1 . . .
  }  
}

menu Channel {
  OTCgpg
  .Authenticate:/verify
  .Ticker:msg %otcgpgbot ;;ticker
  .Ident:msg %otcgpgbot ;;ident $$?="Enter username to identify:"
  .MtGox Live:url -an http://mtgoxlive.com/orders
  .OTC Order Book:url -an http://bitcoin-otc.com/vieworderbook.php
  .Bitcoin
  ..Stats:msg %otcgpgbot ;;bc,stats
  ..Difficulty:msg %otcgpgbot ;;bc,diff
  ..Change in difficulty:msg %otcgpgbot ;;bc,diffchange
  ..Blocks:msg %otcgpgbot ;;bc,blocks
  .Buy/Sell
  ..Buy:msg %otcgpgchan ;;buy $$?="What are you buying?"
  ..Sell:msg %otcgpgchan ;;sell $$?="What are you selling?"
  ..Remove:msg %otcgpgchan ;;remove
  ..Refresh:msg %otcgpgchan ;;refresh
  ..View:msg %otcgpgchan ;;view $$?="Which order #?"
  .WoT
  ..Ratings received
  ...All:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=ANY&type=RECV
    echo $color(info) -st * [OTCgpg] Looking up all ratings received for %otcuser . . .
  }
  ...Positive:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=POS&type=RECV
    echo $color(info) -st * [OTCgpg] Looking up all positive ratings received for %otcuser . . .    
  }
  ...Negative:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=NEG&type=RECV
    echo $color(info) -st * [OTCgpg] Looking up all negative ratings received for %otcuser . . .
  }
  ..Ratings sent
  ...All:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=ANY&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all ratings sent by %otcuser . . .
  }
  ...Positive:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=POS&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all positive ratings sent by %otcuser . . .
  }
  ...Negative:{
    var %otcuser $$?="Enter username:"
    url -an http://bitcoin-otc.com/viewratingdetail.php?nick= $+ %otcuser $+ &sign=NEG&type=SENT
    echo $color(info) -st * [OTCgpg] Looking up all negative ratings sent by %otcuser . . .
  }  
  .Settings
  ..Set verify on join
  ...On:set %otcgpgauto true | echo $color(info) -st * [OTCgpg] GPG autoverify ON with %otcgpgbot for %otcgpguser in %otcgpgchan 
  ...Off:set %otcgpgauto false | echo %color(info) -st * [OTCgpg] GPG autoverify OFF with %otcgpgbot for %otcgpguser in %otcgpgchan
  ..Set GPG bot name:{
    set %otcgpgbot $input(What is the name of the GPG bot?,e,GPG bot name,gribble)
    if (%otcgpgbot == $null) {
      set %otcgpgbot gribble
      echo $color(info) -st * [OTCgpg] Using default GPG bot name of gribble.
    }
  }
  ..Set IRC channel:{
    set %otcgpgchan $input(What is the name of the IRC channel?,e,GPG IRC channel,#bitcoin-otc)
    if (%otcgpgchan == $null) {
      set %otcgpgchan #bitcoin-otc
      echo $color(info) -st * [OTCgpg] Using default IRC channel of #bitcoin-otc.
    }
  }
  ..Set GPG username:{
    set %otcgpguser $input(What is your %otcgpgchan username?,eo,Enter username:,$me)
  }
  ..GPG password
  ...Set/store:{
    set %otcgpgpass $cryptoid($input(What is your GPG password?,po,Enter password:),e
    echo $color(info) -st * [OTCgpg] Your password will be remembered. To clear, type /unset $chr(37) $+ otcgpgpass
  }
  ...Clear:{
    unset %otcgpgpass
    echo $color(info) -st * [OTCgpg] Password cleared. You will be prompted for it in the future.
  }

  ..Set GPG.exe location:/findgpg
  ..Set download method
  ...choose internal (default):{
    set %otcgpgdl true
    echo $color(info) -st * [OTCgpg] Using internal download method for encrypted OTPs.
  }
  ...choose wget:{
    set %otcgpgdl false
    if ($isfile(C:\Cygwin\bin\wget.exe)) {
      set %otcgpgwgetpath "C:\cygwin\bin\wget.exe"
      echo $color(info) -st * [OTCgpg] wget found at C:\cygwin\bin\
    }
    elseif ($isfile(C:\Program Files\GnuWin32\bin\wget.exe)) {
      set %otcgpgwgetpath "C:\Program Files\GnuWin32\bin\wget.exe"
      echo $color(info) -st * [OTCgpg] wget found at C:\Program Files\GnuWin32\bin\
    }
    elseif ($isfile(C:\Program Files (x86)\GnuWin32\bin\wget.exe)) {
      set %otcgpgwgetpath "C:\Program Files (x86)\GnuWin32\bin\wget.exe"
      echo $color(info) -st * [OTCgpg] wget found at C:\Program Files (x86)\GnuWin32\bin\
    }
    else {
      set %otcgpgwgetpath $$?="Can't find wget.exe! Specify the path where it is located:"
      if ($isfile(%otcgpgwgetpath)) {
        set %otcgpgwgetpath $qt(%otcgpgwgetpath)
      }
      else {
        set %otcgpgdl true
        echo $color(info) -st * [OTCgpg] Failed to find wget.exe Reverting to internal download method. . .
      }      
    }
  }
}

on *:LOAD:{
  unset %otcgpg*
  set %otcgpgbot gribble
  set %otcgpgchan #bitcoin-otc
  set %otcgpgdl true

  /findgpg

  while (%otcgpguser == $null) set %otcgpguser $input(What is your %otcgpgchan username?,eo,Enter username:,$me)

  if ($input(Would you like to store your password?,yi,Configuration)) { 
    set %otcgpgpass $cryptoid($input(What is your GPG password?,po,Enter password:),e)
  }
  else {
    unset %otcgpgpass
  }

  if ($input(Would you like to automatically authenticate and verify to %otcgpgbot every time you join %otcgpgchan ?,yi,Configuration)) {
    set %otcgpgauto true
  }
  else {
    set %otcgpgauto false
  }
  echo $color(info) -st * [OTCgpg] The script is now configured and ready. Use /verify to ident to %otcgpgbot and gain voice in %otcgpgchan .
}

alias verify {
  /msg %otcgpgbot ;;eauth %otcgpguser
}

on 1:JOIN:#: {
  if ($nick == $me && %otcgpgauto == true && $chan == %otcgpgchan) {
    echo $color(info) -st * [OTCgpg] Joined %otcgpgchan . Requesting authentication from %otcgpgbot . . .
    msg %otcgpgbot ;;eauth %otcgpguser
  }
}

alias findGPG {
  if ($isfile(C:\Program Files\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\gpg.exe"
    echo $color(info) -st * [OTCgpg] GPG found at C:\Program Files\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files\GNU\GnuPG\pub\gpg.exe"
    echo $color(info) -st * [OTCgpg] GPG found at C:\Program Files\GNU\GnuPG\pub\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\gpg.exe"
    echo $color(info) -st * [OTCgpg] GPG found at C:\Program Files (x86)\GNU\GnuPG\
  }
  elseif ($isfile(C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe)) {
    set %otcgpgpath "C:\Program Files (x86)\GNU\GnuPG\pub\gpg.exe"
    echo $color(info) -st * [OTCgpg] GPG found at C:\Program Files (x86)\GNU\GnuPG\pub\
  }
  else {
    set %otcgpgpath $qt($$?="Please specify the full path/location of gpg.exe:")
  }

  if ($isfile(%otcgpgpath)) {
    echo $color(info) -st * [OTCgpg] Using gpg.exe from %otcgpgpath . 
  }
    else {
      echo $color(info) -st * [OTCgpg] Unable to find GPG. Please try again, or re-load the script by typing /load -rs $script
    }     
}

alias otcgpg_decrypt {
  var %in = $scriptdir $+ $1
  var %out = $scriptdir $+ stdout.txt
  if (%otcgpgpass == $null) {
    var %cmd = -w cmd /C %otcgpgpath --yes --decrypt %in > %out
    echo $color(info) -st * [OTCgpg] You will be prompted by GPG.exe for your password. 
  }
  else {
    var %cmd = -wnh cmd /C echo $cryptoid(%otcgpgpass,d) $+ $chr(124) %otcgpgpath --batch --yes --passphrase-fd 0 --decrypt %in > %out
  }
  xrun %cmd
  .timer 1 10 /otcgpg_everify %out
}

alias otcgpg_everify {
  if ($isfile($1)) {
    var %s = $read($1) 
    /msg %otcgpgbot ;;everify %s
    .remove $1
    if (%otcgpgdl == false) {
      .remove $scriptdir $+ otcgpgkey.txt
    }
  }
  else {
    .timer 1 10 otcgpg_everify $1
    echo $color(info) -st * [OTCgpg] Unable to decrypt the OTP. Incorrect password or there was an error downloading.
  }
}

alias otcgpg_download {
  var %socket $+(otcdl,$chr(46),$nopath($1))
  if (!$sock(%socket)) {
    sockopen %socket $gettok($1,2,47) 80
    sockmark %socket HEAD $gettok($1,2,47) $+($chr(47),$gettok($1,3,47),$chr(47),$gettok($1,4,47))
    echo $color(info) -st * [OTCgpg] Beginning to retrieve OTP.
  }
  else {
    echo $color(info) -st * [OTCgpg] Socket already in use.
  }
}

on *:SOCKOPEN:otcdl.*:{
  hadd -m ticks $sockname $ticks
  var %file = $nopath($gettok($sock($sockname).mark,3,32))
  var %fullfile = $+(",$scriptdir,%file,")
  var %sckr = sockwrite -n $sockname, %^ = $gettok($sock($sockname).mark,3,32)
  echo $color(info) -st * [OTCgpg] Connecting to OTP host. . .
  write -c %fullfile
  %sckr GET $iif(left(%^,1) != $chr(47),$chr(47) $+ %^,%^) HTTP/1.0
  %sckr HOST: $gettok($sock($sockname).mark,2,32)
  %sckr ACCEPT: *.*
  %sckr $crlf
}

on *:SOCKREAD:otcdl.*:{
  if ($sockerr) {
    echo $color(info) -st * [OTCgpg] Error: $sock($sockname).wsmsg
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
        echo $color(info) -st * [OTCgpg] Downloading %totsize bytes. . .
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
  echo $color(info) -st * [OTCgpg] File %filename downloaded in : %ticks seconds. Beginning decryption.
  /otcgpg_decrypt %filename
}

on *:TEXT:$(Request successful for user %otcgpguser $+ *):?:{
  if ($nick == %otcgpgbot && %otcgpgdl == true) {
    /otcgpg_download $wildtok($1-, http://*, 1, 32)
  }
  if ($nick == %otcgpgbot && %otcgpgdl == false) {
    /otcgpg_wget $wildtok($1-, http://*, 1, 32)
  }
}

alias otcgpg_wget {
  xrun -wnh cmd /C %otcgpgwgetpath -O $scriptdir $+ otcgpgkey.txt $1
  otcgpg_decrypt otcgpgkey.txt
}

on *:TEXT:$(You are now authenticated for user %otcgpguser $+ *):?: {
  if ($nick == %otcgpgbot) {
    /msg %otcgpgbot ;;voiceme
    echo $color(info) -st * [OTCgpg] Successfully authenticated to %otcgpgbot . .
  }
}

alias xrun {
  var %a = $ticks, %n = 5, %c = $1-, %b = false
  if -* iswm $1 {
    %c = $2-
    if w isin $1 { %b = true }
    if $regex($1,/((?<=r)[0-9]+|[hnx])/i) { %n = $replace($regml(1),h,0,n,2,x,3) }
  }
  .comopen %a WScript.Shell
  if !$comerr { .comclose %a $com(%a,Run,3,bstr,%c,uint,%n,bool,%b) }
}

alias cryptoid {
  if ($2 == e) {
    var %i = 1, %s = $replace($1-, $chr(32), $chr(1)), %r
    while (%i <= $len($1-)) {
      %r = $instok(%r, $base($calc($asc($mid(%s, %i, 1)) * %i), 10, 16), $calc($numtok(%r, 46) + 1), 46)    
      inc %i
    }
    return %r
  }
  elseif ($2 == d) {
    var %i = 1, %x = $numtok($1-, 46), %r
    while (%i <= %x) {
      %r = $+(%r, $chr($calc($base($gettok($1-, %i, 46), 16, 10) / %i)))
      inc %i    
    }
    return $replace(%r, $chr(1), $chr(32))
    else echo $color(info) -st [OTGgpg] Insufficient parameters.
  }
}