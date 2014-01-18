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
  $sortby = "id";
  $validkeys = array('id', 'buysell', 'nick', 'amount', 'thing', 'price', 'otherthing', 'notes');
  $sortorder = "ASC";

  $typefilter = isset($_GET["type"]) ? $_GET["type"] : "";
  $typefilter = html_entity_decode($typefilter);
  $thingfilter = isset($_GET["thing"]) ? $_GET["thing"] : "";
  $thingfilter = html_entity_decode($thingfilter);
  $otherthingfilter = isset($_GET["otherthing"]) ? $_GET["otherthing"] : "";
  $otherthingfilter = html_entity_decode($otherthingfilter);
  $eitherthingfilter = isset($_GET["eitherthing"]) ? $_GET["eitherthing"] : "";
  $eitherthingfilter = html_entity_decode($eitherthingfilter);
  $nickfilter = isset($_GET["nick"]) ? $_GET["nick"] : "";
  $nickfilter = html_entity_decode($nickfilter);
  $notesfilter = isset($_GET["notes"]) ? $_GET["notes"] : "";
  $notesfilter = html_entity_decode($notesfilter);
  include("somefunctions.php");
  
  $queryfilter = array();
  if ($typefilter != "") $queryfilter[] = "buysell LIKE :buysell";
  if ($thingfilter != "") $queryfilter[] = "thing LIKE :thing";
  if ($nickfilter != "") $queryfilter[] = "nick LIKE :nick";
  if ($otherthingfilter != "") $queryfilter[] = "otherthing LIKE :otherthing";
  if ($eitherthingfilter != "") $queryfilter[] = "(thing LIKE :eitherthing OR otherthing LIKE :eitherthing)";
  if ($notesfilter != "") $queryfilter[] = "notes LIKE :notes";

?>

<h2>OTC Order Book <sup>[<a href="orderbook.json">json</a>]</sup></h2>

<?php
if (sizeof($queryfilter) != 0) {
  echo '<div class="filter">Filtered results. <a href="vieworderbook.php">Clear filter</a></div>';
}
?>

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
<form method="GET" action="vieworderbook.php?">
<select name="type">
<option label="--type--" value="" <?php if (strcasecmp($typefilter, "") == 0) {echo "selected";} ?>>--type--</option>
<option value="BUY" <?php if (strcasecmp($typefilter, "buy") == 0) {echo "selected";} ?>>BUY</option>
<option value="SELL" <?php if (strcasecmp($typefilter, "sell") == 0) {echo "selected";} ?>>SELL</option>
</select>
<select name="nick">
<option label="--nick--" value="" selected>--nick--</option>
<?php
if ($query = $db->Query('SELECT distinct nick FROM orders ORDER BY nick COLLATE NOCASE ASC')){
  while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
    echo '<option value="' . htmlspecialchars($entry['nick']) . '"';
    if (strcasecmp($nickfilter, $entry['nick']) == 0) {echo " selected";}
    echo '>' . htmlspecialchars($entry['nick']) . "</option>\n";
  }
}
?>
</select>
<select name="thing">
<option label="--thing--" value="" selected>--thing--</option>
<?php
if ($query = $db->Query('SELECT distinct upper(thing) AS uthing FROM orders ORDER BY uthing ASC')){
  $thingdata = $query->fetchAll(PDO::FETCH_COLUMN, 0);
  foreach ($thingdata as $thing) {
    echo '<option value="' . htmlspecialchars($thing) . '"';
    if (strcasecmp($thingfilter, $thing) == 0) {echo " selected";}
    echo '>' . htmlspecialchars($thing) . "</option>\n";
  }
}
?>
</select>
<select name="otherthing">
<option label="otherthing" value="" selected>--otherthing--</option>
<?php
if ($query = $db->Query('SELECT distinct upper(otherthing) AS uotherthing FROM orders ORDER BY uotherthing ASC')){
  $otherthingdata = $query->fetchAll(PDO::FETCH_COLUMN, 0);
  foreach ($otherthingdata as $otherthing) {
    echo '<option value="' . htmlspecialchars($otherthing) . '"';
    if (strcasecmp($otherthingfilter, $otherthing) == 0) {echo " selected";}
    echo '>' . htmlspecialchars($otherthing) . "</option>\n";
  }
}
?>
</select>
<select name="eitherthing">
<option label="eitherthing" value="" selected>--eitherthing--</option>
<?php
$eitherthingdata = array_merge($thingdata, $otherthingdata);
sort($eitherthingdata, SORT_STRING);
$eitherthingdata = array_unique($eitherthingdata);
foreach ($eitherthingdata as $eitherthing) {
  echo '<option value="' . htmlspecialchars($eitherthing) . '"';
  if (strcasecmp($eitherthingfilter, $eitherthing) == 0) {echo " selected";}
  echo '>' . htmlspecialchars($eitherthing) . "</option>\n";
}
?>
</select>
<label>Search notes: <input type="text" name="notes" <?php if ($notesfilter != "") {echo 'value="' . htmlspecialchars($notesfilter) . '"';} ?> /></label>
<input type="submit" value="Filter" />
</form>
</td></tr>
</table>

  <table class="datadisplay sortable">
   <tr>
<?php
foreach ($validkeys as $key) $colheaders[$key] = array('linktext' => str_replace("_", " ", $key));
$colheaders["buysell"]["linktext"] = "type";
$colheaders["amount"]["linktext"] = "quantity";
$colheaders["thing"]["linktext"] = "thing";
$colheaders["otherthing"]["linktext"] = "otherthing";
foreach ($colheaders as $by => $colhdr) {
  if ($colhdr["linktext"] != "notes"){
    echo "    <th>" . $colhdr["linktext"] . (!empty($colhdr["othertext"]) ? "<br>".$colhdr["othertext"] : "") . "</th>\n";
  }
  else {
    echo "    <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" . $colhdr["linktext"] . "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" . (!empty($colhdr["othertext"]) ? "<br>".$colhdr["othertext"] : "") . "</th>\n";
  }
}
?>   </tr>
<?php
  if (sizeof($queryfilter) != 0) {
    $queryfilter = " WHERE " . join(' AND ', $queryfilter);
  }
  else {
    $queryfilter = "";
  }
  $sql = 'SELECT id, created_at, refreshed_at, buysell, nick, host, amount, thing, price, otherthing, notes FROM orders ' . $queryfilter . ' ORDER BY id COLLATE NOCASE ASC';
  $sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
  $sth->setFetchMode(PDO::FETCH_ASSOC);
  
  if ($typefilter != "") $sth->bindValue(':buysell',$typefilter);
  if ($thingfilter != "") $sth->bindValue(':thing',$thingfilter);
  if ($nickfilter != "") $sth->bindValue(':nick',$nickfilter);
  if ($otherthingfilter != "") $sth->bindValue(':otherthing',$otherthingfilter);
  if ($eitherthingfilter != "") $sth->bindValue(':eitherthing',$eitherthingfilter);
  if ($notesfilter != "") $sth->bindValue(':notes','%' . $notesfilter . '%');

  $sth->execute();
  if (!$sth)
    echo "   <tr><td>No outstanding orders found</td></tr>\n";
  else {
    $color = 0;
    while ($entry = $sth->fetch(PDO::FETCH_BOTH)) {
      if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>"> 
    <td><a href="vieworder.php?id=<?php echo $entry["id"]; ?>"><?php echo $entry["id"]; ?></a></td>
    <td class="type"><?php echo $entry["buysell"]; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlspecialchars($entry['nick']); ?>"><?php echo htmlspecialchars($entry["nick"]); ?></a></td>
    <td><?php echo $entry["amount"]; ?></td>
    <td class="currency"><?php echo htmlspecialchars($entry["thing"]); ?></td>
    <td class="price"><?php $indp = index_prices($entry["price"]); if (is_numeric($indp)) {printf("%.5g", $indp);} else {echo $indp; } ?></td>
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
