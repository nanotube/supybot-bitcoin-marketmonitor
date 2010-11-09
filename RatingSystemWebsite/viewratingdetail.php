<html>

<head><title>
<?php

$var="sortby";
$sortby = isset($_GET[$var]) ? $_GET[$var] : "rating";
$validkeys = array('id', 'rater_nick', 'rated_nick', 'created_at', 'rating', 'notes');
if (! in_array($sortby, $validkeys)){
    $sortby = "rating";
}

$var="sortorder";
$sortorder = isset($_GET[$var]) ? $_GET[$var] : "ASC";
$validorders = array("ASC","DESC");
if (! in_array($sortorder, $validorders)){
   $sortorder = "ASC";
}

$var="sign";
$sign = isset($_GET[$var]) ? $_GET[$var] : "ANY";
$validvalues = array("ANY","POS","NEG");
if (! in_array($sign, $validvalues)){
   $sign = "ANY";
}

$var="type";
$type = isset($_GET[$var]) ? $_GET[$var] : "RECV";
$validvalues = array("RECV","SENT");
if (! in_array($type, $validvalues)){
   $type = "RECV";
}

$var="nick";
$nick = isset($_GET[$var]) ? $_GET[$var] : "";

echo "Rating details for user " . $nick;

?>
</title>

<style>
<!--
  table.ratingdisplay { border: 1px solid gray; border-collapse: collapse; 
    margin-left: 50px; margin-right: 50px; }
  .ratingdisplay td { border: 1px solid gray; padding: 10px; }
  .ratingdisplay th { border: 1px solid gray; padding: 10px; background-color: #d3d7cf; }
  tr.even { background-color: #dbdfff; }
  h2 { text-align: center; }
-->
</style>

</head>

<body>

<?php
echo '<h2>Rating details for user ' . $nick . '</h2>'. "\n";

echo '<p>[<a href="/">home</a>] || [<a href="/viewratings.php">all users</a>]</p>' . "\n";

$types = array('RECV' => 'received', 'SENT' => 'sent');
$signs = array('ANY' => 'all', 'POS' => 'positive', 'NEG' => 'negative');

echo '<p>You are currently viewing ' . $signs[$sign] . ' ratings ' . $types[$type] . ' by user ' . $nick . ".</p>\n";

echo "<p>\n";
echo '[<a href="viewratingdetail.php?nick=' . $nick . '&sign=' . $sign . '&type=RECV">view received</a>] || ';
echo '[<a href="viewratingdetail.php?nick=' . $nick . '&sign=' . $sign . '&type=SENT">view sent</a>]</p>' . "\n";
echo "<p>\n";
echo '[<a href="viewratingdetail.php?nick=' . $nick . '&type=' . $type . '&sign=POS">view positive</a>] || ';
echo '[<a href="viewratingdetail.php?nick=' . $nick . '&type=' . $type . '&sign=NEG">view negative</a>] || ';
echo '[<a href="viewratingdetail.php?nick=' . $nick . '&type=' . $type . '&sign=ANY">view all</a>]</p>' . "\n";

?>

<h3>Summary statistics</h3>

<ul>
<?php

$typequeries = array('RECV' => 'users.id = ratings.rated_user_id', 'SENT' => 'users.id = ratings.rater_user_id');
$signqueries = array('ANY' => ' ', 'POS' => ' AND ratings.rating > 0', 'NEG' => ' AND ratings.rating < 0');

if ($db = new PDO('sqlite:./otc/RatingSystem.db')) {
    $sql = "SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM users, ratings WHERE users.nick = ? AND " . $typequeries[$type] . $signqueries[$sign];
    $sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
    $sth->execute(array($nick));
    if ($sth == false) {
        echo "<li>No positive ratings found</li>" . "\n";
    }
    $entry = $sth->fetch(PDO::FETCH_BOTH);
    echo "<li>Count of " . $signs[$sign] . " ratings " . $types[$type] . ": " . $entry['ratingcount'] . ". Total of points: " . $entry['ratingsum'] . ".</li>\n";
}
?>
</ul>

<?php
echo '<h3>List of ' . $signs[$sign] . ' ratings ' . $types[$type] . '</h3>'
?>

<table class="ratingdisplay">
<tr>

<?php
$sortorders = array('id' => 'ASC', 'rater_nick' => 'ASC', 'rated_nick' => 'ASC', 'created_at' => 'ASC', 'rating' => 'ASC', 'notes' => 'ASC');
if ($sortorder == 'ASC') {
  $sortorders[$sortby] = 'DESC';
}
echo '  <th><a href="viewratingdetail.php?sortby=id&sortorder=' . $sortorders['id'] . '">id</a></th>' . "\n";
echo '  <th><a href="viewratingdetail.php?sortby=rater_nick&sortorder=' . $sortorders['rater_nick'] . '">rater nick</a></th>' . "\n";
echo '  <th><a href="viewratingdetail.php?sortby=rated_nick&sortorder=' . $sortorders['rated_nick'] . '">rated nick</a></th>' . "\n";
echo '  <th><a href="viewratingdetail.php?sortby=created_at&sortorder=' . $sortorders['created_at'] . '">created at</a><br>(UTC)</th>' . "\n";
echo '  <th><a href="viewratingdetail.php?sortby=rating&sortorder=' . $sortorders['rating'] . '">rating</a></th>' . "\n";
echo '  <th><a href="viewratingdetail.php?sortby=notes&sortorder=' . $sortorders['notes'] . '">notes</a></th>' . "\n";
?>
</tr>

<?php

if ($db = new PDO('sqlite:./otc/RatingSystem.db')) {
   $typequeries = array('RECV' => 'users2.nick = ? AND users2.id = ratings.rated_user_id AND users.id = ratings.rater_user_id', 'SENT' => 'users.nick = ? AND users.id = ratings.rater_user_id AND users2.id = ratings.rated_user_id');
   $signqueries = array('ANY' => ' ', 'POS' => ' AND ratings.rating > 0', 'NEG' => ' AND ratings.rating < 0');

   $sql = "SELECT ratings.id as id, users.nick as rater_nick, users2.nick as rated_nick, ratings.created_at as created_at, ratings.rating as rating, ratings.notes as notes from users, users as users2, ratings WHERE " . $typequeries[$type] . $signqueries[$sign] . " ORDER BY " . $sortby . " " . $sortorder;
   $sth = $db->prepare($sql, array(PDO::ATTR_CURSOR => PDO::CURSOR_FWDONLY));
   $sth->execute(array($nick));
    if ($sth == false) {
        echo "<tr><td>No matching records found</td></tr>" . "\n";
    } 
    else {
        $color = 1;
        //$resultrow = 0;
        //$results = $query->fetchAll(PDO::FETCH_BOTH);
        while ($entry = $sth->fetch(PDO::FETCH_BOTH)) {
            if ($color % 2 == 1){
                echo '<tr class="odd">' . "\n"; 
            }
            else {
                echo '<tr class="even">' . "\n";
            }
            $color = $color + 1;
            echo '  <td>' . $entry['id'] . '</td>' . "\n";
            echo '  <td><a href="viewratingdetail.php?nick=' . $entry['rater_nick'] . '&sign=ANY&type=RECV">' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['rater_nick'])) . '</a></td>' . "\n";
            echo '  <td><a href="viewratingdetail.php?nick=' . $entry['rated_nick'] . '&sign=ANY&type=RECV">' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['rated_nick'])) . '</a></td>' . "\n";
            echo '  <td>' . gmdate('Y-m-d|H:i:s', $entry['created_at']) . '</td>' . "\n";
            echo '  <td>' . $entry['rating'] . '</td>' . "\n";
            echo '  <td>' . $entry['notes'] . '</td>' . "\n";
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
