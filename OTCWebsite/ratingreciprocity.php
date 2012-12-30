<?php
	function like($s, $e) {
		return str_replace(array($e, '_', '%'), array($e.$e, $e.'_', $e.'%'), $s);
	}

	$nick = isset($_GET["nick"]) ? $_GET["nick"] : "";
	$nickfilter = html_entity_decode(like($nick, '|'));
	$nick = html_entity_decode($nick);
	if ($nick == "") header( 'Location: http://bitcoin-otc.com/viewratings.php' );
?>

<?php
	//error_reporting(-1); ini_set('display_errors', 1);
	$sortby = "rating";
	$sortorder = "ASC";
	$validkeys = array('rater_nick', 'rating_sent', 'rating_received', 'rated_nick');

	$outformat = isset($_GET["outformat"]) ? $_GET["outformat"] : "";
	$outformat = html_entity_decode($outformat);
?>
<?php
	try { $db = new PDO('sqlite:./otc/RatingSystem.db'); }
	catch (PDOException $e) { die($e->getMessage()); }

	include('querytojson.php');
	if ($outformat == 'json'){
		$sql = "SELECT users.nick as rater_nick, users2.nick as rated_nick, ratings.rating as rating from users, users as users2, ratings WHERE users.id = ratings.rater_user_id AND users2.id = ratings.rated_user_id AND (users.nick LIKE ? ESCAPE '|' OR users2.nick LIKE ? ESCAPE '|');";
		$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
		$sth->setFetchMode(PDO::FETCH_ASSOC);
		$sth->execute(array($nickfilter, $nickfilter));
		if (!$sth) echo "[]";
		else	jsonOutput($sth);
		exit();
	}
	
?>

<!DOCTYPE html>

<?php
 $pagetitle = "Rating Details for User '" . htmlentities($nick) . "'";
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
<a href="viewratings.php">Web of Trust Data</a> &rsaquo;
Rating Symmetry for <?php echo htmlentities($nick); ?>
</div>

  <h3>About <?php echo htmlentities($nick); ?></h3>
  <ul>
<?php
	echo '<li><a href="viewgpg.php?nick=' . htmlentities($nick) . '">GPG identity</a></li>';
	echo '<li><a href="viewratingdetail.php?nick=' . htmlentities($nick) . '">Rating detail</a></li>';
?>
  </ul>
  <h3>Rating exchanges<sup>[<a href="<?php jsonlink(); ?>">json</a>]</sup></h3>
  
<?php
	$results = array();
	$sql = "SELECT users.nick as rater_nick, users2.nick as rated_nick, ratings.rating as rating from users, users as users2, ratings WHERE users.id = ratings.rater_user_id AND users2.id = ratings.rated_user_id AND (users.nick LIKE ? ESCAPE '|' OR users2.nick LIKE ? ESCAPE '|');";
	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
	$sth->execute(array($nickfilter, $nickfilter));
	if (!$sth) echo "<tr><td>No matching records found</td></tr>\n";
	else {
		while ($entry = $sth->fetch(PDO::FETCH_BOTH)) {
			if ($entry['rater_nick'] == $nick){
				if (array_key_exists($entry['rated_nick'], $results)){
					$results[$entry['rated_nick']]['rating_sent'] = $entry['rating'];
				} else {
					$results[$entry['rated_nick']] = array('rater_nick' => $entry['rater_nick'],
																					'rating_sent' => $entry['rating'],
																					'rating_received' => 'unrated',
																					'rated_nick' => $entry['rated_nick']);
				}
			} else {
				if (array_key_exists($entry['rater_nick'], $results)){
					$results[$entry['rater_nick']]['rating_received'] = $entry['rating'];
				} else {
					$results[$entry['rater_nick']] = array('rater_nick' => $entry['rated_nick'],
																					'rating_sent' => 'unrated',
																					'rating_received' => $entry['rating'],
																					'rated_nick' => $entry['rater_nick']);
				}
			}
		}
	}
?>

  <table class="datadisplay sortable">
   <tr>
<?php
	foreach ($validkeys as $key) $colheaders[$key] = array('linktext' => str_replace("_", " ", $key));
	foreach ($colheaders as $by => $colhdr) {
		echo "    <th>" . $colhdr["linktext"] . (!empty($colhdr["othertext"]) ? "<br>".$colhdr["othertext"] : "")."</th>\n";
	}
?>
   </tr>
<?php
	$color = 0;
	foreach ($results as $row) {
		if ($color++ % 2) $class="even"; else $class="odd";
?>
   <tr class="<?php echo $class; ?>">
    <td><?php echo htmlentities($row['rater_nick']); ?></td>
    <td><?php echo $row['rating_sent']; ?></td>
	<td><?php echo $row['rating_received']; ?></td>
	<td><a href="ratingreciprocity.php?nick=<?php echo htmlentities($row['rated_nick']); ?>"><?php echo htmlentities($row['rated_nick']); ?></a></td>
   </tr>
<?
		}
?>
  </table>

<?php
 include("footer.php");
?>

 </body>
</html>
