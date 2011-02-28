<!DOCTYPE html>
<?php
  include("somefunctions.php");
?>

<?php
 $pagetitle = "#bitcoin-otc currency ticker";
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo; 
<a href="vieworderbook.php">Order Book</a> &rsaquo;
Ticker
</div>

<h2>#bitcoin-otc currency ticker</h2>

<p>The ticker table is constructed from all orders of BTC against one of the supported <a href="currencycodes.php">currency codes</a>. If you want your order to be included, make sure to use one of the supported currency codes. Just as importantly - if you have a non-standard order on the book (loans, futures, options, etc.), please use a non-standard currency code so as not to skew the quote list.</p>

<p>This data feed is updated every 5 minutes.</p>

<?php
     	try { $db = new PDO('sqlite:./OTCQuotes.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
?>
  <table class="datadisplay">
     <tr>
    <th>currency</th>
    <th>bid</th>
    <th>ask</th>
   </tr>
<?php
  if (!$query = $db->Query('SELECT currency, bid, ask FROM quotes ORDER BY currency ASC'))
    echo "   <tr><td>No data found</td></tr>\n";
  else {
   while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
    if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>"> 
    <td><a href = "http://bitcoin-otc.com/vieworderbook.php?sortby=buysell&eitherthing=<?php echo $entry['currency']; ?>"><?php echo $entry['currency']; ?></a></td>
    <td><?php echo $entry['bid']; ?></td>
    <td><?php echo $entry['ask']; ?></td>
   </tr>
<?
  }
}
?>

  </table>

<p><a href="quotes.json">JSON data</a></p>

<?php
 include("footer.php");
?>

 </body>
</html>
