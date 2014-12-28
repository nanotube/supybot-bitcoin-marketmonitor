<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-type" content="text/html;charset=UTF-8">
    <title>#bitoin-otc</title>
    <link rel="stylesheet" type="text/css" href="css/indexstyle.css"/>
    <link rel="shortcut icon" href="favicon.ico"/>

    <script src="sorttable.js"></script>
</head>
<body>
<nav>
    <a class="brand" href="http://bitcoin-otc.com">
        <img src="http://bitcoin-otc.com/pink_btc_135x135.png">

        <h1>#bitcoin-otc</h1>
    </a>

    <div class="links">
        <div><a href="http://bitcoin-otc.com">Home</a></div>
        <div><a href="http://bitcoin-otc.com/viewratings.php">Web of Trust</a></div>
        <div><a href="http://bitcoin-otc.com/vieworderbook.php">Order Book</a></div>
        <div><a href="http://wiki.bitcoin-otc.com">Wiki</a></div>
        <div><a href="http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc">Help</a></div>
        <div><a href="contact.php">Contact</a></div>
    </div>
</nav>
<div class="readable">
    <h1>#bitcoin-otc Marketplace</h1>

    <p>
        #bitcoin-otc is an <a href="http://en.wikipedia.org/wiki/Over-the-counter_(finance)">over-the-counter</a>
        marketplace for trading with the <a href="http://bitcoin.org">BitCoin</a> currency. The marketplace, where
        over-the-counter trading takes place, is located in the #bitcoin-otc channel on the
        <a href="http://freenode.net">Freenode</a> IRC network. If you don't have an IRC client,
        <a href="http://webchat.freenode.net/?channels=#bitcoin-otc">click here</a> to visit the channel with
        your web browser.
    </p>

    <h4>Resources</h4>
    <ul>
        <li><a href="vieworderbook.php">Web view of the open order book</a>.
        <li><a href="ticker.php">Currency ticker</a>.
        <li><a href="http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc">A guide to using #bitcoin-otc</a>. A must-read
            for all users: how to use the order book, and how to stay safe while conducting OTC transactions.
    </ul>

    <hr>

    <h2>OTC Web of Trust</h2>

    <p>
        To complement the OTC marketplace, we offer a web of trust service. Due to the p2p nature of OTC transactions,
        you are exposed to <a href="http://en.wikipedia.org/wiki/Credit_risk#Counterparty_risk">counter-party risk</a>.
        Having access to an account of your counter-party's reputation and trade history can greatly mitigate the risk
        involved in conducting such transactions. This is precisely the kind of information that the OTC web of trust
        provides.
    </p>

    <h4>Resources</h4>
    <ul>
        <li><a href="trust.php">OTC web of trust homepage</a>
        <li><a href="viewratings.php">Explore the trust database</a>
        <li><a href="http://wiki.bitcoin-otc.com/wiki/OTC_Rating_System">Guide to using the web of trust</a>
        <li><a href="viewgpg.php">Registered user GPG keys</a>
    </ul>

    <hr>

    <h2>Disclaimers</h2>

    <p>
        #bitcoin-otc is merely an aggregator of outstanding supply and demand. All transactions that may occur are
        conducted directly between <a href="https://en.wikipedia.org/wiki/Counterparty">counter-parties</a>,
        without any participation or mediation from #bitcoin-otc. As such, it is each individual's responsibility
        to conduct due diligence with regards to their counter-parties, and otherwise act in a prudent way to avoid
        falling prey to fraudulent users. It is strongly recommended that all users review the
        <a href="http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc">guide to using #bitcoin-otc</a>, which contains
        a non-exhaustive list of suggestions for safe conduct on #bitcoin-otc.
    </p>

    <p>
        The OTC web of trust is not foolproof. Do not rely on the ratings blindly; since the cost of entry into the web
        of trust is only one positive rating, it is not impossible for a fraudulent user to infiltrate the system and
        create a number of bogus accounts which all inter-rate each other. Talk to people on #bitcoin-otc first, make
        sure they are familiar with the person you're about to trade with, have traded with them successfully in the
        past, etc.
    </p>

    <h2>Code</h2>

    <p>
        The code for the order book IRC bot plugin, the OTC web of trust bot plugin, as well as this website is
        open-source.
        Feel free to grab it from <a href="http://github.com/nanotube/supybot-bitcoin-marketmonitor">GitHub</a>.
        Improvements and contributions are welcome. If you would like to post questions or bug reports, please use the
        <a href="https://github.com/nanotube/supybot-bitcoin-marketmonitor/issues">issues tracker</a> contained in the
        GitHub repository.
    </p>
</div>
<div class="sponsors">
    <h4>Support our Sponsors</h4>
    <a href="https://www.privateinternetaccess.com/pages/buy-vpn/OTC001">
        <img src="pia.png" title="Private Internet Access VPN" alt="Private Internet Access graphic">
    </a>
    <a href="http://coinabul.com/?a=247">
        <img src="coinabul.jpg" title="Coinabul Bitcoin-to-Gold Dealer" alt="Coinabul Graphic">
    </a>
    <a href="http://www.dragons.tl/launchpad.php?referrer=bitcoinotc">
        <img src="dragonstale.jpg" title="Dragon's Tale MMO" alt="Dragon's Tale Graphic">
    </a>
</div>
<?php
include("footer.php");
?>
</body>
</html>
