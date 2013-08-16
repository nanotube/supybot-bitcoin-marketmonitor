<?php
  $notesfilter = isset($_GET["notes"]) ? $_GET["notes"] : "";
  $notesfilter = html_entity_decode($notesfilter);
  if ($notesfilter == "") header( 'Location: http://bitcoin-otc.com/viewratings.php' );
?>

<!DOCTYPE html>
<?php
 $pagetitle = "#bitcoin-otc web of trust data";
 include("header.php");
?>

<div class="breadcrumbs">
<a href="/">Home</a> &rsaquo;
<a href="trust.php">Web of Trust</a> &rsaquo;
<a href="viewratings.php">Web of Trust Data</a> &rsaquo;
Ratings filter
</div>

<h2>Ratings filter</h2>

<?php
if (sizeof($notesfilter) != 0) {
  echo '<div class="filter">Filtered results. <a href="viewratings.php">Clear filter</a></div>';
}
?>

<table class="datadisplay" style="width: 100%;">
<tr>
<td style="text-align: left;">
<form method="GET" action="ratingsfilter.php?">
<label>Search notes: <input type="text" name="notes" value="<?php echo htmlspecialchars($notesfilter); ?>"/></label>
<input type="submit" value="Filter" />
</form>
</td>
</tr>
</table>

<table class="datadisplay sortable">
<tr>
 <th>id</th>
 <th>rater nick</th>
 <th>rated nick</th>
 <th>created at<br>(UTC)</th>
 <th>rating</th>
 <th>notes</th>
</tr>

<?php
	try { $db = new PDO('sqlite:./otc/RatingSystem.db'); }
	catch (PDOException $e) { die($e->getMessage()); }
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
	$sql = "SELECT ratings.id as id, users.nick as rater_nick, users2.nick as rated_nick, ratings.created_at as created_at, ratings.rating as rating, ratings.notes as notes from users, users as users2, ratings WHERE users2.id = ratings.rated_user_id AND users.id = ratings.rater_user_id AND notes LIKE ?";
    
    try {	$sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY)); }
    catch (PDOException $e) { die($e->getMessage()); }
	$sth->execute(array('%' . $notesfilter . '%'));
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