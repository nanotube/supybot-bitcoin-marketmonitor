<!DOCTYPE html>
<?php
  $id = isset($_GET["id"]) ? $_GET["id"] : "0";
  if (! is_numeric($id)) $id = 0;
  $validkeys = array('id', 'created_at', 'refreshed_at', 'buysell', 'nick', 'host', 'amount', 'thing', 'price', 'indexedprice', 'otherthing', 'notes');
  include("somefunctions.php");
?>

<?php
 $pagetitle = "#bitcoin-otc order id " . $id;
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo; 
<a href="vieworderbook.php">Order Book</a> &rsaquo;
Order <?php echo $id; ?>
</div>

  <h2>#bitcoin-otc order id <?php echo $id; ?></h2>

<?php
     	try { $db = new PDO('sqlite:./otc/OTCOrderBook.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
?>
  <table class="datadisplay">
<?php
  if (!$query = $db->Query('SELECT id, created_at, refreshed_at, buysell, nick, host, amount, thing, price, otherthing, notes FROM orders WHERE id=' . $id ))
    echo "   <tr><td>No matching orders found</td></tr>\n";
  else {
    if( $entry = $query->fetch(PDO::FETCH_BOTH)){
      $entry["indexedprice"] = index_prices($entry["price"]);
?>
   <tr>
    <th>id</th>
    <td><?php echo $entry["id"]; ?></td>
   </tr>
   <tr>
    <th>created at</th>
    <td><?php echo gmdate("Y-m-d H:i:s", $entry["created_at"]); ?></td>
   </tr>
   <tr>
    <th>refreshed at</th>
    <td><?php echo gmdate("Y-m-d H:i:s", $entry["refreshed_at"]); ?></td>
   </tr>
   <tr>
    <th>type</th>
    <td><?php echo $entry["buysell"]; ?></td>
   </tr>
   <tr>
    <th>nick</th>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlentities($entry['nick']); ?>"><?php echo htmlentities($entry["nick"]); ?></a></td>
   </tr>
   <tr>
    <th>host</th>
    <td><?php echo $entry["host"]; ?></td>
   </tr>
   <tr>
    <th>amount</th>
    <td><?php echo $entry["amount"]; ?></td>
   </tr>
   <tr>
    <th>thing</th>
    <td><?php echo htmlentities($entry["thing"]); ?></td>
   </tr>
   <tr>
    <th>price</th>
    <td><?php echo $entry["indexedprice"]; ?></td>
   </tr>
   <tr>
    <th>raw price</th>
    <td><?php echo $entry["price"]; ?></td>
   </tr>
   <tr>
    <th>other thing</th>
    <td><?php echo htmlentities($entry["otherthing"]); ?></td>
   </tr>
   <tr>
    <th>notes</th>
    <td><?php echo htmlentities($entry["notes"]); ?></td>
   </tr>
<?
  }
  else {
    echo "   <tr><td>No matching orders found</td></tr>\n";
  }
}
?>

  </table>

<?php
 include("footer.php");
?>

 </body>
</html>
