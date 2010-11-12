<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$validkeys = array(
		'id',
		'rater_nick',
		'rated_nick',
		'created_at',
		'rating',
		'notes'
	);
	$sortby = isset($_GET["sortby"]) ? $_GET["sortby"] : "rating";
	if (!in_array($sortby, $validkeys)) $sortby = "rating";

	$validorders = array(
		"ASC",
		"DESC"
	);
	$sortorder = isset($_GET["sortorder"]) ? $_GET["sortorder"] : "ASC";
	if (!in_array($sortorder, $validorders)) $sortorder = "ASC";

	$validvalues = array(
		"ANY",
		"POS",
		"NEG"
	);
	$sign = isset($_GET["sign"]) ? $_GET["sign"] : "ANY";
	if (!in_array($sign, $validvalues)) $sign = "ANY";

	$validvalues = array(
		"RECV",
		"SENT"
	);
	$type = isset($_GET["type"]) ? $_GET["type"] : "RECV";
	if (!in_array($type, $validvalues)) $type = "RECV";
?><!DOCTYPE html><html>
 <head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
  <title>Rating details for user <?php $nick = isset($_GET["nick"]) ? $_GET["nick"] : ""; echo $nick; ?></title>
  <style><!--
	body {
		background-color: #FFFFFF;
		color: #000000;
	}
	h2 {
		text-align: center;
	}
	table.ratingdisplay {
		border: 1px solid gray;
		border-collapse: collapse; 
		margin-left: 50px;
		margin-right: 50px;
	}
	table.ratingdisplay td {
		border: 1px solid gray;
		padding: 10px;
	}
	table.ratingdisplay td.nowrap {
		white-space: nowrap;
	}
	table.ratingdisplay th {
		border: 1px solid gray;
		padding: 10px;
		background-color: #d3d7cf;
	}
	tr.even {
		background-color: #dbdfff;
	}
  --></style>
 </head>
 <body>
  <h2>Rating details for user <?php echo $nick; ?></h2>
  <p>[<a href="/">home</a>] || [<a href="/viewratings.php">all users</a>]</p>
<?php
	$types = array('RECV' => 'received', 'SENT' => 'sent');
	$signs = array('ANY' => 'all', 'POS' => 'positive', 'NEG' => 'negative');
?>
  <p>You are currently viewing <?php echo $signs[$sign]; ?> ratings <?php echo $types[$type]; ?> by user <?php echo $nick; ?>.</p>
  <p>
   [<a href="viewratingdetail.php?nick=<?php echo $nick; ?>&amp;sign=<?php echo $sign; ?>&amp;type=RECV">view received</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo $nick; ?>&amp;sign=<?php echo $sign; ?>&amp;type=SENT">view sent</a>]
  </p>
  <p>
   [<a href="viewratingdetail.php?nick=<?php echo $nick; ?>&amp;type=<?php echo $type; ?>&amp;sign=POS">view positive</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo $nick; ?>&amp;type=<?php echo $type; ?>&amp;sign=NEG">view negative</a>] ||
   [<a href="viewratingdetail.php?nick=<?php echo $nick; ?>&amp;type=<?php echo $type; ?>&amp;sign=ANY">view all</a>]
  </p>
  <h3>Summary statistics</h3>
  <ul>
<?php
	$typequeries = array('RECV' => 'users.id = ratings.rated_user_id', 'SENT' => 'users.id = ratings.rater_user_id');
	$signqueries = array('ANY' => ' ', 'POS' => ' AND ratings.rating > 0', 'NEG' => ' AND ratings.rating < 0');

	try { $db = new PDO('sqlite:./otc/RatingSystem.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
	$sql = "SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM users, ratings WHERE users.nick = ? AND " . $typequeries[$type] . $signqueries[$sign];
	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
	if (!$sth->execute(array($nick))) echo "<li>No positive ratings found</li>\n";
	else {
		$entry = $sth->fetch(PDO::FETCH_BOTH);
		echo "<li>Count of " . $signs[$sign] . " ratings " . $types[$type] . ": " . number_format($entry['ratingcount']) . ". Total of points: " . number_format($entry['ratingsum']) . ".</li>\n";
	}
?>
  </ul>
  <h3>List of <?php echo $signs[$sign]; ?> ratings <?php echo $types[$type]; ?></h3>
  <table class="ratingdisplay">
   <tr>
<?php
	foreach ($validkeys as $key) $sortorders[$key] = array('order' => 'ASC', 'linktext' => str_replace("_", " ", $key));
	if ($sortorder == 'ASC') $sortorders[$sortby]["order"] = 'DESC';
	$sortorders["created_at"]["othertext"] = "(UTC)";
	foreach ($sortorders as $by => $order) {
		//if ($by == $sortby) $order["order"] = "DESC";
		echo "    <th class=\"".str_replace(" ", "_", $order["linktext"])."\"><a href=\"viewratingdetail.php?sortby=$by&amp;sortorder=".$order["order"]."\">".$order["linktext"]."</a>".(!empty($order["othertext"]) ? "<br>".$order["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	$typequeries = array('RECV' => 'users2.nick = ? AND users2.id = ratings.rated_user_id AND users.id = ratings.rater_user_id', 'SENT' => 'users.nick = ? AND users.id = ratings.rater_user_id AND users2.id = ratings.rated_user_id');
	//$signqueries = array('ANY' => ' ', 'POS' => ' AND ratings.rating > 0', 'NEG' => ' AND ratings.rating < 0');
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
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['rater_nick']; ?>&amp;sign=ANY&amp;type=RECV"><?php echo htmlspecialchars($entry['rater_nick']); ?></a></td>
    <td><a href="viewratingdetail.php?nick=<?php echo $entry['rated_nick']; ?>&amp;sign=ANY&amp;type=RECV"><?php echo htmlspecialchars($entry['rated_nick']); ?></a></td>
    <td class="nowrap"><?php echo gmdate('Y-m-d H:i:s', $entry['created_at']); ?></td>
    <td><?php echo $entry['rating']; ?></td>
    <td><?php echo $entry['notes']; ?></td>
   </tr>
<?
		}
	}
?>
  </table>
  <p>[<a href="/">home</a>]</p>
 </body>
</html>