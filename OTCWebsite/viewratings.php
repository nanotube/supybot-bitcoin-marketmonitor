<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc web of trust data";
 include("header.php");
?>

<?php
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "total_rating";
	$validkeys = array('id', 'nick', 'created_at', 'keyid', 'total_rating', 'pos_rating_recv_count', 'neg_rating_recv_count', 'pos_rating_sent_count', 'neg_rating_sent_count');
	if (!in_array($sortby, $validkeys)) $sortby = "total_rating";

	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	if (! isset($_GET[$var]) && $sortby == "total_rating" ) $sortorder = "DESC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
Web of Trust Data
</div>

  <h3>Summary statistics on web of trust</h3>
  <ul><?php
	try { $db = new PDO('sqlite:./otc/RatingSystem.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
	if (!$query = $db->Query('SELECT count(*) as usercount, sum(total_rating) as ratingsum FROM users'))
		echo "<li>No outstanding orders found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "<li>" . $entry['usercount'] . " users in database, with a total of " . $entry['ratingsum'] . " net rating points.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM ratings WHERE rating > 0"))
		echo "<li>No positive ratings found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "<li>" . $entry['ratingcount'] . " positive ratings sent, for a total of " . $entry['ratingsum'] . " points.</li>\n";
	}

	if (!$query = $db->Query("SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM ratings WHERE rating < 0"))
		echo "<li>No negative ratings found</li>\n";
	else {
		$entry = $query->fetch(PDO::FETCH_BOTH);
		echo "<li>" . $entry['ratingcount'] . " negative ratings sent, for a total of " . $entry['ratingsum'] . " points.</li>\n";
	}
?>
  </ul>
  <h3>List of users and ratings</h3>
  <table class="datadisplay">
   <tr>
<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == 'ASC') $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["created_at"]["othertext"] = "(UTC)";
	$sortorders["pos_rating_recv_count"]["linktext"] = "number of positive ratings received";
	$sortorders["neg_rating_recv_count"]["linktext"] = "number of negative ratings received";
	$sortorders["pos_rating_sent_count"]["linktext"] = "number of positive ratings sent";
	$sortorders["neg_rating_sent_count"]["linktext"] = "number of negative ratings sent";
	foreach ($sortorders as $by => $order) {
		//if ($by == $sortby) $order["order"] = "DESC";
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"viewratings.php?sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	$query = $db->Query("attach database './otc/GPG.db' as gpg");
	if (!$query = $db->Query('select rsusers.*, gpg.users.keyid from main.users as rsusers left outer join gpg.users on rsusers.nick LIKE gpg.users.nick ORDER BY ' . $sortby . ' COLLATE NOCASE ' . $sortorder))
		echo "<tr><td>No users found</td></tr>\n";
	else {
		//$resultrow = 0;
		//$results = $query->fetchAll(PDO::FETCH_BOTH);
		$color = 0;
		while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo $entry['id']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=ANY&type=RECV"><?php echo htmlspecialchars($entry['nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['created_at']); ?></td>
	<td><a href="viewgpg.php?nick=<?php echo $entry['nick']; ?>"><?php echo $entry['keyid']; ?></a></td>
    <td><?php echo $entry['total_rating']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=POS&type=RECV"><?php echo $entry['pos_rating_recv_count']; ?></a></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=NEG&type=RECV"><?php echo $entry['neg_rating_recv_count']; ?></a></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=POS&type=SENT"><?php echo $entry['pos_rating_sent_count']; ?></a></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['nick']; ?>&sign=NEG&type=SENT"><?php echo $entry['neg_rating_sent_count']; ?></a></td>
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