<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc web of trust";
 include("header.php");
?>
<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
Web of Trust
</div>
 <div style="float: right; padding-left: 10px; padding-bottom: 10px; text-align: center; font-family: Helvetica;">
   Visit our sponsor:<br>
   <a href="http://www.dragons.tl/launchpad.php?referrer=bitcoinotc"><img src="./dragonstale.jpg" style="border-style: none;"></a>
  </div>
  <h2>What is the OTC web of trust?</h2>
  <p><a href="http://bitcoin-otc.com">#bitcoin-otc</a> is an <a href="http://en.wikipedia.org/wiki/Over-the-counter_(finance)">over-the-counter</a> marketplace for <a href="http://bitcoin.org">bitcoin</a> currency. The marketplace is located in #bitcoin-otc channel on the <a href="http://freenode.net">freenode</a> IRC network.</p>
  <p>Since all transactions carry with them counterparty risk (risk of non-payment by one of the parties), it becomes important to keep track of people's reputations and trade histories, so that you can decrease your probability of getting ripped off. And thus, the OTC web of trust is born.</p>
  <h2>Useful resources</h2>
  <p>The following resources are available for you:</p>
  <ul>
   <li><a href="viewratings.php">Web view of the rating system</a>. You can view the aggregate ratings, as well as explore the detailed ratings sent and received by any given individual.
   <li><a href="http://wiki.bitcoin-otc.com/wiki/OTC_Rating_System">A guide to using the OTC web of trust</a>. A must-read for all users: how to send/update/retract ratings, and guidelines for trust levels.
   <li><a href="http://wiki.bitcoin-otc.com/wiki/User_GPG_keys">List of known user GPG keys</a>.
  </ul>
  <h2>Disclaimers</h2>
  <p>Do not rely on the ratings blindly - since the cost of entry into the web of trust is only one positive rating, it is not impossible for a scammer to infiltrate the system, and then create a bunch of bogus accounts who all inter-rate each other. Talk to people on #bitcoin-otc first, make sure they are familiar with the person you're about to trade with, have traded with him successfully in the past, etc.</p>
  <h2>Code</h2>
  <p>The code for the web of trust IRC bot plugin as well as this website is open. Feel free to grab it from <a href="http://github.com/nanotube/supybot-bitcoin-marketmonitor">this github git repository</a>. Improvements and contributions are welcome. If you would like to post questions or bug reports, please use the issues tracker on github for this repository.</p>
  </div>
 
 <?php
 include("footer.php");
?>
 
 </body>
</html>
