<!DOCTYPE html>

<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "rating";
	$validkeys = array('id', 'rater_nick', 'rated_nick', 'created_at', 'rating', 'notes');
	if (!in_array($sortby, $validkeys)) $sortby = "rating";
	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	$validorders = array("ASC","DESC");
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";
	$sign = isset($_GET["sign"]) ? $_GET["sign"] : "ANY";
	$validvalues = array("ANY","POS","NEG");
	if (!in_array($sign, $validvalues)) $sign = "ANY";
	$type = isset($_GET["type"]) ? $_GET["type"] : "RECV";
	$validvalues = array("RECV","SENT");
	if (!in_array($type, $validvalues)) $type = "RECV";
	$nick = isset($_GET["nick"]) ? $_GET["nick"] : "";
	$nick = html_entity_decode($nick);
?>

<?php
 $pagetitle = "Rating Details for User '" . htmlentities($nick) . "'";
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
<a href="viewratings.php">Web of Trust Data</a> &rsaquo;
Rating for <?php echo htmlentities($nick); ?>
</div>

<?php
	$types = array('RECV' => 'received', 'SENT' => 'sent');
	$signs = array('ANY' => 'all', 'POS' => 'positive', 'NEG' => 'negative');
?>
  <p>You are currently viewing <?php echo $signs[$sign]; ?> ratings <?php echo $types[$type]; ?> by user <?php echo htmlentities($nick); ?>.</p>
  <p>
   [<a href="viewratingdetail.php?nick=<?php echo htmlentities($nick); ?>&sign=<?php echo $sign; ?>&type=RECV">view received</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo htmlentities($nick); ?>&sign=<?php echo $sign; ?>&type=SENT">view sent</a>]
  </p>
  <p>
   [<a href="viewratingdetail.php?nick=<?php echo htmlentities($nick); ?>&type=<?php echo $type; ?>&sign=POS">view positive</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo htmlentities($nick); ?>&type=<?php echo $type; ?>&sign=NEG">view negative</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo htmlentities($nick); ?>&type=<?php echo $type; ?>&sign=ANY">view all</a>]
  </p>
  <h3>About <?php echo htmlentities($nick); ?></h3>
  <ul>
<?php
	$typequeries = array('RECV' => 'users.id = ratings.rated_user_id', 'SENT' => 'users.id = ratings.rater_user_id');
	$signqueries = array('ANY' => ' ', 'POS' => ' AND ratings.rating > 0', 'NEG' => ' AND ratings.rating < 0');

	try { $db = new PDO('sqlite:./otc/RatingSystem.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
	$sql = "SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM users, ratings WHERE users.nick LIKE ? AND " . $typequeries[$type] . $signqueries[$sign];
	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
	if (!$sth->execute(array($nick))) echo "<li>No positive ratings found</li>\n";
	else {
		$entry = $sth->fetch(PDO::FETCH_BOTH);
		echo "<li>Count of " . $signs[$sign] . " ratings " . $types[$type] . ": " . number_format($entry['ratingcount']) . ". Total of points: " . number_format($entry['ratingsum']) . ".</li>\n";
	}
	echo '<li><a href="viewgpg.php?nick=' . htmlentities($nick) . '">GPG identity</a></li>';
?>
  </ul>
  <h3>List of <?php echo $signs[$sign]; ?> ratings <?php echo $types[$type]; ?></h3>
  <table class="datadisplay">
   <tr>
<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == 'ASC') $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["created_at"]["othertext"] = "(UTC)";
	foreach ($sortorders as $by => $order) {
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"viewratingdetail.php?nick=" . htmlentities($nick) . "&sign=$sign&type=$type&sortby=$by&sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	if ($sortby == 'id') $sortby = "ratings.id";
	if ($sortby == 'created_at') $sortby = "ratings.created_at";
	$typequeries = array('RECV' => 'users2.nick LIKE ? AND users2.id = ratings.rated_user_id AND users.id = ratings.rater_user_id', 'SENT' => 'users.nick LIKE ? AND users.id = ratings.rater_user_id AND users2.id = ratings.rated_user_id');
	$sql = "SELECT ratings.id as id, users.nick as rater_nick, users2.nick as rated_nick, ratings.created_at as created_at, ratings.rating as rating, ratings.notes as notes from users, users as users2, ratings WHERE " . $typequeries[$type] . $signqueries[$sign] . " ORDER BY " . $sortby . " " . $sortorder;
	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
	$sth->execute(array($nick));
	if (!$sth) echo "<tr><td>No matching records found</td></tr>\n";
	else {
		//$resultrow = 0;
		//$results = $query->fetchAll(PDO::FETCH_BOTH);
		$color = 0;
		while ($entry = $sth->fetch(PDO::FETCH_BOTH)) {
			if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo $entry['id']; ?></td>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlentities($entry['rater_nick']); ?>&sign=ANY&type=RECV"><?php echo htmlentities($entry['rater_nick']); ?></a></td>
    <td><a href="viewratingdetail.php?nick=<?php echo htmlentities($entry['rated_nick']); ?>&sign=ANY&type=RECV"><?php echo htmlentities($entry['rated_nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['created_at']); ?></td>
    <td><?php echo $entry['rating']; ?></td>
    <td><?php echo htmlentities($entry['notes']); ?></td>
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
