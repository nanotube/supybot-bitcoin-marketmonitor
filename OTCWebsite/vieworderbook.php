<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc order book";
 include("header.php");
?>
<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo; Order Book
</div>

<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "price";
	$validkeys = array('id', 'buysell', 'nick', 'amount', 'thing', 'price', 'otherthing', 'notes');
	if (!in_array($sortby, $validkeys)) $sortby = "price";
	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";

	include("somefunctions.php");
	
?>
  <h3>Summary statistics on outstanding orders</h3>
  <ul><?php
	try { $db = new PDO('sqlite:./otc/OTCOrderBook.db'); }
	catch (PDOException $e) { die($e->getMessage()); }

	if (!$query = $db->Query('SELECT count(*) as ordercount FROM orders'))
		echo "   <li>No outstanding orders found</li>";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding orders.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ordercount FROM orders WHERE buysell='BUY'"))
		echo "   <li>No outstanding BUY orders found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding BUY orders.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ordercount FROM orders WHERE buysell='SELL'"))
		echo "   <li>No outstanding SELL orders found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding SELL orders.</li>\n";
	}
?>  </ul>
  <h3>List of outstanding orders</h3>
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
	if (!$query = $db->Query('SELECT id, created_at, refreshed_at, buysell, nick, host, amount, thing, price, otherthing, notes FROM orders ORDER BY ' . sqlite_escape_string($sortby) . ' ' . sqlite_escape_string($sortorder) ))
		echo "   <tr><td>No outstanding orders found</td></tr>\n";
	else {
		//$resultrow = 0;
		//$results = $query->fetchAll(PDO::FETCH_BOTH);
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