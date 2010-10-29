<html>

<head><title>
<?php

$var="sortby";
$sortby = isset($_GET[$var]) ? $_GET[$var] : "keys.key";
$validkeys = array('id','created_at', 'refreshed_at', 'buysell', 'nick', 'host', 'btcamount', 'price', 'notes');
if (! in_array($sortby, $validkeys)){
    $sortby = "price";
}

$var="sortorder";
$sortorder = isset($_GET[$var]) ? $_GET[$var] : "ASC";
$validorders = array("ASC","DESC");
if (! in_array($sortorder, $validorders)){
    $sortorder = "ASC";
}

echo "#bitcoin-otc order book";

?>
</title>

<style>
<!--
  table.orderbookdisplay { border: 1px solid gray; border-collapse: collapse; 
    margin-left: 50px; margin-right: 50px; }
  .orderbookdisplay td { border: 1px solid gray; padding: 10px; }
  .orderbookdisplay th { border: 1px solid gray; padding: 10px; background-color: #d3d7cf; }
  tr.even { background-color: #dbdfff; }
  h2 { text-align: center; }
-->
</style>

</head>

<body>

<h2>#bitcoin-otc order book</h2>

<p>[<a href="/">home</a>]</p>

<h3>Summary statistics on outstanding orders</h3>

<ul>
<?php
if ($db = new PDO('sqlite:./otc/OTCOrderBook.db')) {
   $query = $db->Query('SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders');
    if ($query == false) {
        echo "<li>No outstanding orders found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['ordercount'] . " outstanding orders, for a total of " . $entry['ordersum'] . " BTC.</li>\n";

    $query = $db->Query("SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders WHERE buysell='BUY'");
    if ($query == false) {
        echo "<li>No outstanding BUY orders found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['ordercount'] . " outstanding BUY orders, for a total of " . $entry['ordersum'] . " BTC.</li>\n";

    $query = $db->Query("SELECT count(*) as ordercount, sum(btcamount) as ordersum FROM orders WHERE buysell='SELL'");
    if ($query == false) {
        echo "<li>No outstanding SELL orders found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['ordercount'] . " outstanding SELL orders, for a total of " . $entry['ordersum'] . " BTC.</li>\n";
}
//$totaltxfile = fopen("txcount.txt", "r");
//$txcount = fread($totaltxfile, 4096);
//echo "<li>" . $txcount . "transactions are known to have occurred on #bitcoin-otc.</li>\n";
?>
</ul>

<h3>List of outstanding orders</h3>

<table class="orderbookdisplay">
<tr>

<?php
//$validkeys = array('id','created_at', 'refreshed_at', 'buysell', 'nick', 'host', 'btcamount', 'price', 'notes');
$sortorders = array('id' => 'ASC', 'created_at' => 'ASC', 'refreshed_at' => 'ASC', 'buysell' => 'ASC', 'nick' => 'ASC', 'host' => 'ASC', 'btcamount' => 'ASC', 'price' => 'ASC', 'notes' => 'ASC');
if ($sortorder == 'ASC') {
  $sortorders[$sortby] = 'DESC';
}
echo '  <th><a href="vieworderbook.php?db=&sortby=id&sortorder=' . $sortorders['multikey'] . '">id</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=created_at&sortorder=' . $sortorders['created_at'] . '">created at</a><br>(UTC)</th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=refreshed_at&sortorder=' . $sortorders['refreshed_at'] . '">refreshed at</a><br>(UTC)</th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=buysell&sortorder=' . $sortorders['buysell'] . '">type</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=nick&sortorder=' . $sortorders['nick'] . '">nick</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=host&sortorder=' . $sortorders['host'] . '">host</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=btcamount&sortorder=' . $sortorders['btcamount'] . '">BTC amount</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=price&sortorder=' . $sortorders['price'] . '">price</a></th>' . "\n";
echo '  <th><a href="vieworderbook.php?db=&sortby=othercurrency&sortorder=' . $sortorders['othercurrency'] . '">currency</a></th>' . "\n";
echo '  <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="vieworderbook.php?db=&sortby=notes&sortorder=' . $sortorders['notes'] . '">notes</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>' . "\n";
?>
</tr>

<?php

if ($db = new PDO('sqlite:./otc/OTCOrderBook.db')) {
   $query = $db->Query('SELECT id, created_at, refreshed_at, buysell, nick, host, btcamount, price, othercurrency, notes FROM orders ORDER BY othercurrency, ' . $sortby . ' ' . $sortorder );
    if ($query == false) {
        echo "<tr><td>No outstanding orders found</td></tr>" . "\n";
    } 
    else {
        $color = 1;
        //$resultrow = 0;
        //$results = $query->fetchAll(PDO::FETCH_BOTH);
        while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
            if ($color % 2 == 1){
                echo '<tr class="odd">' . "\n"; 
            }
            else {
                echo '<tr class="even">' . "\n";
            }
            $color = $color + 1;
            echo '  <td>' . $entry['id'] . '</td>' . "\n";
            echo '  <td>' . gmdate('Y-m-d|H:i:s', $entry['created_at']) . '</td>' . "\n";
            echo '  <td>' . gmdate('Y-m-d|H:i:s', $entry['refreshed_at']) . '</td>' . "\n";
            echo '  <td>' . $entry['buysell'] . '</td>' . "\n";
            echo '  <td>' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['nick'])) . '</td>' . "\n";
            echo '  <td>' . $entry['host'] . '</td>' . "\n";
            echo '  <td>' . $entry['btcamount'] . '</td>' . "\n";
            echo '  <td>' . $entry['price'] . '</td>' . "\n";
            echo '  <td>' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['othercurrency'])) . '</td>' . "\n";
            echo '  <td>' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['notes'])) . '</td>' . "\n";
            echo '</tr>' . "\n";
        }
    }
} else {
    die($err);
}

?>
</table>

<p>[<a href="/">home</a>]</p>

</body>
</html>
