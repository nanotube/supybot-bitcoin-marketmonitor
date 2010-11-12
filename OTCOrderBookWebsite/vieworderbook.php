<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$validkeys = array('id',
		'created_at',
		'refreshed_at',
		'buysell',
		'nick',
		'host',
		'btcamount',
		'price',
		'othercurrency',
		'notes'
	);
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "price";
	if (!in_array($sortby, $validkeys)) $sortby = "price";

	$validorders = array(
		"ASC",
		"DESC"
	);
	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";
?><!DOCTYPE html><html>
 <head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
  <script src="jquery-1.4.3.min.js" type="text/javascript"></script>
  <script src="jquery.ba-bbq.min.js" type="text/javascript"></script>
  <script src="filter.orderbook.js" type="text/javascript"></script>
  <style><!--
	body {
		background-color: #FFFFFF;
		color: #000000;
	}
	h2 {
		text-align: center;
	}
	table.orderbookdisplay {
		border: 1px solid gray;
		border-collapse: collapse;
		width: 100%;
	}
	table.orderbookdisplay td {
		border: 1px solid gray;
		padding: 4px;
	}
	table.orderbookdisplay td.nowrap {
		white-space: nowrap;
	}
	table.orderbookdisplay th {
		background-color: #d3d7cf;
		border: 1px solid gray;
		padding: 10px;
		vertical-align: top;
	}
	tr.even {
		background-color: #dbdfff;
	}
  --></style>
  <title>#bitcoin-otc order book</title>
 </head>
 <body>
  <h2>#bitcoin-otc order book</h2>
  <p>[<a href="/">home</a>]</p>
  <h3>Summary statistics on outstanding orders</h3>
  <ul>
<?php
	try { $db = new PDO('sqlite:./otc/OTCOrderBook.db'); }
	catch (PDOException $e) { die($e->getMessage()); }

	if (!$query = $db->Query('SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders'))
		echo "   <li>No outstanding orders found</li>";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding orders, for a total of " . number_format($entry['ordersum'], 1) . " BTC.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders WHERE buysell='BUY'"))
		echo "   <li>No outstanding BUY orders found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding BUY orders, for a total of " . number_format($entry['ordersum'], 1) . " BTC.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders WHERE buysell='SELL'"))
		echo "   <li>No outstanding SELL orders found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "   <li>" . number_format($entry['ordercount']) . " outstanding SELL orders, for a total of " . number_format($entry['ordersum'], 1) . " BTC.</li>\n";
	}

	//$totaltxfile = fopen("txcount.txt", "r");
	//$txcount = fread($totaltxfile, 4096);
	//echo "<li>" . $txcount . "transactions are known to have occurred on #bitcoin-otc.</li>\n";
?>  </ul>
  <h3>List of outstanding orders</h3>
  <table class="orderbookdisplay">
   <tr>
<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == "ASC") $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["created_at"]["othertext"] = "(UTC)";
	$sortorders["refreshed_at"]["othertext"] = "(UTC)";
	$sortorders["buysell"]["linktext"] = "type";
	$sortorders["btcamount"]["linktext"] = "BTC amount";
	$sortorders["othercurrency"]["linktext"] = "currency";
	foreach ($sortorders as $by => $order) {
		//if ($by == $sortby) $order["order"] = "DESC";
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"vieworderbook.php?sortby=$by&amp;sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>   </tr>
<?php
	if (!$query = $db->Query('SELECT id, created_at, refreshed_at, buysell, nick, host, btcamount, price, othercurrency, notes FROM orders ORDER BY ' . $sortby . ' ' . $sortorder ))
		echo "   <tr><td>No outstanding orders found</td></tr>\n";
	else {
		//$resultrow = 0;
		//$results = $query->fetchAll(PDO::FETCH_BOTH);
		$color = 0;
		while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>"> 
    <td><?php echo $entry["id"]; ?></td>
    <td class="nowrap"><?php echo gmdate("Y-m-d H:i:s", $entry["created_at"]); ?></td>
    <td class="nowrap"><?php echo gmdate("Y-m-d H:i:s", $entry["refreshed_at"]); ?></td>
    <td class="type"><?php echo $entry["buysell"]; ?></td>
    <td><a href="http://trust.bitcoin-otc.com/viewratingdetail.php?nick=<?php echo $entry['nick']; ?>"><?php echo htmlspecialchars($entry["nick"]); ?></a></td>
    <td class="nowrap"><?php echo $entry["host"]; ?></td>
    <td><?php echo $entry["btcamount"]; ?></td>
    <td class="price"><?php echo $entry["price"]; ?></td>
    <td class="currency"><?php echo htmlspecialchars($entry["othercurrency"]); ?></td>
    <td><?php echo htmlspecialchars($entry["notes"]); ?></td>
   </tr>
<?
		}
	}
?>  </table>
  <p>[<a href="/">home</a>]</p>
 </body>
</html>