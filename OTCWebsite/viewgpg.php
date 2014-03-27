<?php

	function like($s, $e) {
		return str_replace(array($e, '_', '%'), array($e.$e, $e.'_', $e.'%'), $s);
	}

	$sortby = "nick";
	$validkeys = array('id', 'nick', 'registered_at', 'keyid', 'fingerprint', 'bitcoinaddress', 'last_authed_at');

	$sortorder = "ASC";
	
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
	if ($nickfilter != "") $queryfilter[] = "nick LIKE :nick ESCAPE '|'";
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
		$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
		$sth->setFetchMode(PDO::FETCH_ASSOC);
		if ($nickfilter != "") $sth->bindValue(':nick', like($nickfilter, '|'));
		$sth->execute();

		if (!$sth)
			echo "[]";
		else
			jsonOutput($sth);
		exit();
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
	echo "GPG Key for " . htmlspecialchars($nickfilter);
}
else {
	echo "GPG Key database";
}
?>
</div>

  <h3>#bitcoin-otc gpg key data <?php if ($nickfilter != ""){echo "for user " . htmlspecialchars($nickfilter) ;} ?> <sup>[<a href="<?php jsonlink(); ?>">json</a>]</sup></h3>
  <table class="datadisplay sortable">
   <tr>

<?php
	foreach ($validkeys as $key) $colheaders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	$colheaders["registered_at"]["othertext"] = "(UTC)";
	$colheaders["last_authed_at"]["othertext"] = "(UTC)";
	foreach ($colheaders as $by => $colhdr) {
		echo "    <th>" . $colhdr["linktext"] . (!empty($colhdr["othertext"]) ? "<br>".$colhdr["othertext"] : "") . "</th>\n";
	}
?>
   </tr>
<?php
	$sql = 'SELECT * FROM users ' . $queryfilter . 'ORDER BY nick COLLATE NOCASE ASC';
	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
	$sth->setFetchMode(PDO::FETCH_ASSOC);
	if ($nickfilter != "") $sth->bindValue(':nick', like($nickfilter, '|'));
	$sth->execute();

	if (!$sth)
		echo "<tr><td>No users found</td></tr>\n";
	else {
		$color = 0;
		while ($entry = $sth->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo $entry['id']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlspecialchars($entry['nick']); ?>&sign=ANY&type=RECV"><?php echo htmlspecialchars($entry['nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['registered_at']); ?></td>
    <td><?php echo $entry['keyid']; ?></td>
	<td><a href ="http://pool.sks-keyservers.net:11371/pks/lookup?op=vindex&search=0x<?php echo $entry['fingerprint']; ?>"><?php echo $entry['fingerprint']; ?></a></td>
	<td><?php echo $entry['bitcoinaddress']; ?></td>
	<td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['last_authed_at']); ?></td>
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