/*    
    GPG authentication helper script for mIRC. 
    
    Version 1.0.

    Usage: /verify

    You can install this script by typing /load -rs <path-to-script>

    You can also just copy/paste it into 'remote' window and then hit the OK button.

    You must change gpg.user (16 char hex), gpg.pass, and, probably, gpg.path

    Use /reload -rs <path-to-script> if you make changes after the installation.
 
    joric/bitcoin-otc, public domain.
*/

alias gpg.user return GPG_USER_ID
alias gpg.pass return GPG_PASSPHRASE
alias gpg.path return C:\Progra~1\GNU\GnuPG\gpg.exe
alias gpg.host return bitcoin-otc.com
alias gpg.bot return gribble

alias verify {
    /msg gribble ;;gpg eauth $me
}

on *:TEXT:*encrypted*:?: { 
    if ($nick == gribble) {
        /gpg_download $gpg.host /otps/ $+ $gpg.user
    }
}

alias gpg_download {     
    var %socket $+(dl,$chr(46),$nopath($2))
    if (!$sock(%socket)) {
      sockopen %socket $1 80
      sockmark %socket HEAD $1 $2
      echo $color(info) -s * Download started.
    }
    else { 
        echo $color(info) -s * Socket already in use. 
    }
}   

on *:SOCKOPEN:dl.*:{
  hadd -m ticks $sockname $ticks
  var %file = $nopath($gettok($sock($sockname).mark,3,32))
  var %fullfile = $+(",$scriptdir,%file,")
  var %sckr = sockwrite -n $sockname, %^ = $gettok($sock($sockname).mark,3,32)
  echo $color(info) -s * Connecting to host...
  write -c %fullfile
  %sckr GET $iif(left(%^,1) != $chr(47),$chr(47) $+ %^,%^) HTTP/1.0
  %sckr HOST: $gettok($sock($sockname).mark,2,32)
  %sckr ACCEPT: *.* 
  %sckr $crlf
}

on *:SOCKREAD:dl.*:{
    if ($sockerr) {
        echo $color(info) -s * Error: $sock($sockname).wsmsg
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
                echo $color(info) -s * Downloading %totsize bytes...
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

on *:SOCKCLOSE:dl.*:{
    var %ticks = $calc(($ticks - $hget(ticks,$sockname)) /1000)
    var %filename = $nopath($gettok($sock($sockname).mark,3,32))
    echo $color(info) -s * File %filename downloaded in : %ticks seconds.
    /gpg_decrypt %filename
}

alias gpg_decrypt {
    var %in = $scriptdir $+ $1
    var %out = $scriptdir $+ stdout.txt
    var %cmd = cmd /C echo $gpg.pass $+ $chr(124) $gpg.path --passphrase-fd 0 --decrypt %in > %out
    /run -np %cmd
    /timer1 1 2 /gpg_everify %out
}

alias gpg_everify {
    fopen f $1
    %s = $fread(f)
    fclose f
    /msg $gpg.bot ;;gpg everify %s
    echo $color(info) -s * Script finished.
}