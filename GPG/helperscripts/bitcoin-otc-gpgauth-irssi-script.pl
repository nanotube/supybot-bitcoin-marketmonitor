use Irssi;
use File::Temp qw/ tempfile /;
use RPC::XML;
use RPC::XML::Client;
use strict;
use vars qw($VERSION %IRSSI $registernick $authnick $challenge);

$VERSION = '0.01';
%IRSSI = (
    authors     => 'Philippe Gauthier',
    contact     => 'philippe.gauthier\@deuxpi.ca',
    name        => 'bitcoin-otc-gpgauth',
    description => 'GPG authentication for #bitcoin-otc',
    license     => 'GPL',
    url         => 'http://www.deuxpi.ca/irssi/',
    changed     => 'Tue Mar  8 17:42 EST 2011'
);

# Modify for your nickname and the last 16 hex digits of your key Id.
my %nickname_keys = (
    lc('my_nickname') => 'B426AAD45E36F46C'
);

sub cmd_register {
    my ($data, $server, $witem) = @_;

    if (!$server || !$server->{'connected'}) {
        Irssi::print("Not connected to a server.");
        return;
    }

    if (!$witem || $witem->{type} ne "CHANNEL") {
        Irssi::print("Not an active channel window.");
        return;
    }

    my $nick;

    if ($data eq '') {
        $nick = $server->{'nick'};
    } else {
        $nick = $data;
    }

    if (!defined $nickname_keys{lc $nick}) {
        $witem->print("Please add the key Id for $nick to bitcoin-otc-gpgauth.pl");
        return;
    }

    my $keyid = $nickname_keys{lc $nick};

    $witem->command("MSG ".$witem->{name}." ;;gpg register $nick $keyid");
    $registernick = $nick;
}

sub cmd_auth {
    my ($data, $server, $witem) = @_;

    if (!$server || !$server->{'connected'}) {
        Irssi::print("Not connected to a server.");
        return;
    }

    if (!$witem || $witem->{type} ne "CHANNEL") {
        Irssi::print("Not an active channel window.");
        return;
    }

    if ($data eq '') {
        $authnick = $server->{'nick'};
    } else {
        $authnick = $data;
    }

    $witem->command("MSG ".$witem->{name}." ;;gpg auth $authnick");
}

sub cmd_pass {
    my ($data, $server, $witem) = @_;

    if (!$server || !$server->{'connected'}) {
        Irssi::print("Not connected to a server.");
        return;
    }

    if (!$witem || $witem->{type} ne "CHANNEL") {
        Irssi::print("Not an active channel window.");
        return;
    }

    if (!defined $challenge) {
        $witem->print("No challenge received yet.");
        return;
    }

    my $nick;
    if (defined $registernick) {
        $nick = $registernick;
        undef $registernick;
    } elsif (defined $authnick) {
        $nick = $authnick;
        undef $authnick;
    }
    my $keyid = $nickname_keys{lc $nick};
    my $passphrase = $data;

    my ($fh, $cleartext) = tempfile();
    open my $file, '+>', $cleartext;
    print $file $challenge;
    close $file;

    my ($fh, $output) = tempfile();

    my $result = `echo "$passphrase" | gpg --quiet --batch --yes --status-fd 1 --passphrase-fd 0 --default-key $keyid! --output $output --clearsign $cleartext | grep "[GNUPG:]"`;
    unlink($cleartext);

    local $/;
    open my $input, '<', $output;
    my $sig = <$input>;
    close $input;

    if ((my $i = index($result, "GOOD_PASSPHRASE")) > -1) {
        my $cli = RPC::XML::Client->new('http://paste.pocoo.org/xmlrpc/');
        my $req = RPC::XML::request->new('pastes.newPaste',
            RPC::XML::string->new('text'),
            RPC::XML::string->new($sig));
        my $resp = $cli->send_request($req);
        my $url = "http://paste.pocoo.org/raw/".$resp->value."/";
        $witem->command("MSG ".$witem->{name}." ;;gpg verify $url");
    } else {
        $witem->print("Invalid passphrase");
    }

    unlink($output);
}

sub event_notice {
    my ($server, $msg, $nick, $address, $target) = @_;

    return unless $nick eq 'gribble';
    return unless $target eq '#bitcoin-otc';
    return unless (defined $registernick or defined $authnick);

    if ($msg =~ /Your challenge string is: (.+)$/) {
        $challenge = $1;
        Irssi::active_win()->print("Use the '/gpgpass PASSPHRASE' command to enter your passphrase.");
    }
}

Irssi::command_bind('gpgregister', 'cmd_register');
Irssi::command_bind('gpgauth', 'cmd_auth');
Irssi::command_bind('gpgpass', 'cmd_pass');
Irssi::signal_add('message public', 'event_notice');
