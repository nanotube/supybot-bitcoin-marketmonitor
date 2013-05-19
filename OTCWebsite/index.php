<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc";
 include("header.php");
?>
<div class="breadcrumbs">
<a href="/">Home</a>
</div>
  <div style="float: left; width: 180px; text-align: center;">
   <div style="padding-left: 10px; padding-bottom: 10px; text-align: center; font-family: Helvetica;">
    Visit our sponsors:<br>
    <a href="https://www.privateinternetaccess.com/pages/buy-vpn/OTC001"><img src="pia.png" title="Private Internet Access VPN" alt="Private Internet Access graphic" style="border-style: none;"></a>
    <hr style="width: 80%;">
    <a href="http://coinabul.com/?a=247"><img src="coinabul.jpg" title="Coinabul Bitcoin-to-Gold Dealer" alt="Coinabul Graphic" style="border-style: none;"></a>
    <hr style="width: 80%;">
    <a href="http://www.dragons.tl/launchpad.php?referrer=bitcoinotc"><img src="dragonstale.jpg" title="Dragon's Tale MMO" alt="Dragon's Tale Graphic" style="border-style: none;"></a>
   </div>
  </div>
  <div style="padding-left: 200px;">
   <div class="contentbox">
    <h2 style="text-align: center;">#bitcoin-otc marketplace</h2>
    <p>#bitcoin-otc is an <a href="http://en.wikipedia.org/wiki/Over-the-counter_(finance)">over-the-counter</a> marketplace for trading with <a href="http://bitcoin.org">bitcoin</a>. The marketplace is located in #bitcoin-otc channel on the <a href="http://freenode.net">freenode</a> IRC network. If you don't have an IRC client, <a href="http://webchat.freenode.net/?channels=#bitcoin-otc">click here</a> to visit the channel with your web browser.</p>

    <h4>resources</h4>
    <ul>
     <li><a href="vieworderbook.php">Web view of the open order book</a>.
     <li><a href="ticker.php">Currency ticker</a>.
     <li><a href="http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc">A guide to using #bitcoin-otc</a>. A must-read for all users: how to use the order book, and how to stay safe while conducting OTC transactions.
    </ul>
   </div>

   <div class="contentbox">
    <h2 style="text-align: center;">OTC web of trust</h2>
    To complement the OTC marketplace, we offer a web of trust service. Due to the p2p nature of OTC transactions, you are exposed to <a href="http://en.wikipedia.org/wiki/Credit_risk#Counterparty_risk">counterparty risk</a>. To mitigate this risk, you need to have access to your counterparty's reputation and trade history. This is precisely the kind of information that the OTC web of trust provides.
    <h4>resources</h4>
    <ul>
     <li><a href="trust.php">OTC web of trust homepage</a>
     <li><a href="viewratings.php">Explore the trust database</a>
     <li><a href="http://wiki.bitcoin-otc.com/wiki/OTC_Rating_System">Guide to using the web of trust</a>
     <li><a href="viewgpg.php">Registered user GPG keys</a>
    </ul>
   </div>

   <div style="float: left; margin-bottom: 20px;">
    <h2>Disclaimers</h2>
    <p>#bitcoin-otc is merely an aggregator of outstanding supply and demand. All transactions that may occur are conducted directly between counterparties, without any participation or intermediation from #bitcoin-otc. As such, it is each individual's responsibility to conduct due diligence on their counterparties, and otherwise act in a prudent way to avoid falling prey to fraudulent users. It is strongly recommended that all users review the <a href="http://wiki.bitcoin-otc.com/wiki/Using_bitcoin-otc">guide to using #bitcoin-otc</a>, which contains a non-exhaustive list of suggestions for safe conduct on #bitcoin-otc.</p>
    <p>The OTC web of trust is not foolproof. Do not rely on the ratings blindly - since the cost of entry into the web of trust is only one positive rating, it is not impossible for a scammer to infiltrate the system, and then create a bunch of bogus accounts who all inter-rate each other. Talk to people on #bitcoin-otc first, make sure they are familiar with the person you're about to trade with, have traded with him successfully in the past, etc.</p>
    <h2>Code</h2>
    The code for the order book IRC bot plugin, the OTC web of trust bot plugin, as well as this website is open. Feel free to grab it from <a href="http://github.com/nanotube/supybot-bitcoin-marketmonitor">this github git repository</a>. Improvements and contributions are welcome. If you would like to post questions or bug reports, please use the issues tracker on github for this repository.
    </div>
   </div>
<?php
 include("footer.php");
?>
 </body>
</html>
