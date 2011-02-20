<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc order book";
 include("header.php");
?>
<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo; 
<a href="vieworderbook.php">Order Book</a>
</div>

<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "price";
	$validkeys = array('id', 'buysell', 'nick', 'amount', 'thing', 'price', 'otherthing', 'notes');
	if (!in_array($sortby, $validkeys)) $sortby = "price";
	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";

	$typefilter = isset($_GET["type"]) ? $_GET["type"] : "";
	$thingfilter = isset($_GET["thing"]) ? $_GET["thing"] : "";
	$otherthingfilter = isset($_GET["otherthing"]) ? $_GET["otherthing"] : "";
    $nickfilter = isset($_GET["nick"]) ? $_GET["nick"] : "";

	include("somefunctions.php");
	
?>

<h2>OTC Order Book</h2>

<table class="datadisplay" style="width: 100%;">
<tr>
  <?php
    try { $db = new PDO('sqlite:./otc/OTCOrderBook.db'); }
    catch (PDOException $e) { die($e->getMessage()); }

    echo ' <td style="text-align: center;">Total orders<br>';
    if (!$query = $db->Query('SELECT count(*) as ordercount FROM orders'))
      echo "0";
    else {
      $entry = $query->fetch(PDO::FETCH_BOTH);
      echo number_format($entry['ordercount']);
    }
    echo "</td>\n";

    echo ' <td style="text-align: center;">Buy orders<br>';
    if (!$query = $db->Query("SELECT count(*) as ordercount FROM orders WHERE buysell='BUY'"))
      echo "0";
    else {
      $entry = $query->fetch(PDO::FETCH_BOTH);
      echo number_format($entry['ordercount']);
    }
    echo "</td>\n";

    echo ' <td style="text-align: center;">Sell orders<br>';
    if (!$query = $db->Query("SELECT count(*) as ordercount FROM orders WHERE buysell='SELL'"))
      echo "0";
    else {
      $entry = $query->fetch(PDO::FETCH_BOTH);
      echo number_format($entry['ordercount']);
    }
    echo "</td>\n";
?>

<td style="text-align: right;">
<form method="GET" action="vieworderbook.php">
<select name="type">
<option label="--type--" value="" selected>--type--</option>
<option value="BUY">BUY</option>
<option value="SELL">SELL</option>
</select>
<select name="nick">
<option label="--nick--" value="" selected>--nick--</option>
<?php
if ($query = $db->Query('SELECT distinct nick FROM orders ORDER BY nick COLLATE NOCASE ASC')){
  while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
    echo '<option value="' . $entry['nick'] . '">' . $entry['nick'] . "</option>\n";
  }
}
?>
</select>
<select name="thing">
<option label="--thing--" value="" selected>--thing--</option>
<?php
if ($query = $db->Query('SELECT distinct upper(thing) AS uthing FROM orders ORDER BY uthing ASC')){
  while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
    echo '<option value="' . $entry['uthing'] . '">' . $entry['uthing'] . "</option>\n";
  }
}
?>
</select>
<select name="otherthing">
<option label="otherthing" value="" selected>--otherthing--</option>
<?php
if ($query = $db->Query('SELECT distinct upper(otherthing) AS uotherthing FROM orders ORDER BY uotherthing ASC')){
  while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
    echo '<option value="' . $entry['uotherthing'] . '">' . $entry['uotherthing'] . "</option>\n";
  }
}
?>
</select>
<input type="submit" value="Filter" />
</form>
</td></tr>
</table>

  <table class="datadisplay">
   <tr>
<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == "ASC") $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["buysell"]["linktext"] = "type";
	$sortorders["amount"]["linktext"] = "amount";
	$sortorders["thing"]["linktext"] = "thing";
	$sortorders["otherthing"]["linktext"] = "otherthing";
	foreach ($sortorders as $by => $order) {
		if ($order["linktext"] != "notes"){
			echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"vieworderbook.php?sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
		}
		else {
			echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"vieworderbook.php?sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
		}
	}
?>   </tr>
<?php
   $queryfilter = array();
   if ($typefilter != "") $queryfilter[] = "buysell LIKE '" . sqlite_escape_string($typefilter) . "'";
   if ($thingfilter != "") $queryfilter[] = "thing LIKE '" . sqlite_escape_string($thingfilter) . "'";
   if ($nickfilter != "") $queryfilter[] = "nick LIKE '" . sqlite_escape_string($nickfilter) . "'";
   if ($otherthingfilter != "") $queryfilter[] = "otherthing LIKE '" . sqlite_escape_string($otherthingfilter) . "'";
   if (sizeof($queryfilter) != 0) {
     $queryfilter = " WHERE " . join(' AND ', $queryfilter);
   }
   else {
     $queryfilter = "";
   }
   $sql = 'SELECT id, created_at, refreshed_at, buysell, nick, host, amount, thing, price, otherthing, notes FROM orders ' . $queryfilter . ' ORDER BY ' . sqlite_escape_string($sortby) . ' ' . sqlite_escape_string($sortorder);
   if (!$query = $db->Query($sql))
     echo "   <tr><td>No outstanding orders found</td></tr>\n";
   else {
     $color = 0;
     while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
       if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>"> 
    <td><a href="vieworder.php?id=<?php echo $entry["id"]; ?>"><?php echo $entry["id"]; ?></a></td>
    <td class="type"><?php echo $entry["buysell"]; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>"><?php echo htmlspecialchars($entry["nick"]); ?></a></td>
    <td><?php echo $entry["amount"]; ?></td>
    <td class="currency"><?php echo htmlspecialchars($entry["thing"]); ?></td>
    <td class="price"><?php printf("%.5g", index_prices($entry["price"])); ?></td>
    <td class="currency"><?php echo htmlspecialchars($entry["otherthing"]); ?></td>
    <td><?php echo htmlspecialchars($entry["notes"]); ?></td>
   </tr>
<?
     }
   }
?>  </table>

<?php
 include("footer.php");
?>

</body>
</html>
