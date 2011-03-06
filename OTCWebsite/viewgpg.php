<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc gpg key database";
 include("header.php");
?>

<?php
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "nick";
	$validkeys = array('id', 'nick', 'registered_at', 'keyid', 'fingerprint');
	if (!in_array($sortby, $validkeys)) $sortby = "nick";

	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	if (! isset($_GET[$var]) && $sortby == "total_rating" ) $sortorder = "DESC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
GPG Key database
</div>

  <h3>#bitcoin-otc gpg key database</h3>
  <table class="datadisplay">
   <tr>

<?php
	try { $db = new PDO('sqlite:./otc/GPG.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
?>

<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == 'ASC') $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["registered_at"]["othertext"] = "(UTC)";
	foreach ($sortorders as $by => $order) {
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"viewgpg.php?sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	if (!$query = $db->Query('SELECT * FROM users ORDER BY ' . $sortby . ' ' . $sortorder))
		echo "<tr><td>No users found</td></tr>\n";
	else {
		$color = 0;
		while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo $entry['id']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=ANY&type=RECV"><?php echo htmlspecialchars($entry['nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['registered_at']); ?></td>
    <td><?php echo $entry['keyid']; ?></td>
	<td><?php echo $entry['fingerprint']; ?></td>
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