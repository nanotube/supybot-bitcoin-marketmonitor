<?php
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "nick";
	$validkeys = array('id', 'nick', 'registered_at', 'keyid', 'fingerprint');
	if (!in_array($sortby, $validkeys)) $sortby = "nick";

	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	if (! isset($_GET[$var]) && $sortby == "total_rating" ) $sortorder = "DESC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";
	
	$nickfilter = isset($_GET["nick"]) ? $_GET["nick"] : "";
	$nickfilter = html_entity_decode($nickfilter);
	
	$outformat = isset($_GET["outformat"]) ? $_GET["outformat"] : "";
	$outformat = html_entity_decode($outformat);
?>
<?php
	try { $db = new PDO('sqlite:./otc/GPG.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
?>
<?php
	$queryfilter = array();
	if ($nickfilter != "") $queryfilter[] = "nick LIKE '" . sqlite_escape_string($nickfilter) . "'";
	if (sizeof($queryfilter) != 0) {
		$queryfilter = " WHERE " . join(' AND ', $queryfilter);
	}
	else {
		$queryfilter = "";
	}
?>
<?php
	include('querytojson.php');
	if ($outformat == 'json'){
		$sql = 'SELECT * FROM users ' . $queryfilter;
		if (!$query = $db->Query($sql, PDO::FETCH_ASSOC))
			echo "[]";
		else {
			jsonOutput($query);
			exit();
		}
	}
?>

<!DOCTYPE html>

<?php
 $pagetitle = "#bitcoin-otc gpg key data";
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
<?php
if ($nickfilter != ""){
	echo '<a href="viewgpg.php">GPG Key database</a> &rsaquo;';
	echo "GPG Key for " . htmlentities($nickfilter);
}
else {
	echo "GPG Key database";
}
?>
</div>

  <h3>#bitcoin-otc gpg key data <?php if ($nickfilter != ""){echo "for user " . htmlentities($nickfilter) ;} ?></h3>
  <table class="datadisplay">
   <tr>

<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == 'ASC') $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["registered_at"]["othertext"] = "(UTC)";
	foreach ($sortorders as $by => $order) {
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"viewgpg.php?nick=" . htmlentities($nickfilter) . "&sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	$sql = 'SELECT * FROM users ' . $queryfilter . 'ORDER BY ' . sqlite_escape_string($sortby) . ' COLLATE NOCASE ' . sqlite_escape_string($sortorder);
	if (!$query = $db->Query($sql))
		echo "<tr><td>No users found</td></tr>\n";
	else {
		$color = 0;
		while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo $entry['id']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlentities($entry['nick']); ?>&sign=ANY&type=RECV"><?php echo htmlentities($entry['nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['registered_at']); ?></td>
    <td><?php echo $entry['keyid']; ?></td>
	<td><a href ="http://pool.sks-keyservers.net:11371/pks/lookup?op=vindex&search=0x<?php echo $entry['fingerprint']; ?>"><?php echo $entry['fingerprint']; ?></a></td>
   </tr>
<?
		}
	}
?>
  </table>

<?php
 include("footer.php");
?>

 </body>
</html>