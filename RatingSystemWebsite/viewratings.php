<html>

<head><title>
<?php

$var="sortby";
$sortby = isset($_GET[$var]) ? $_GET[$var] : "keys.key";
$validkeys = array('id', 'nick', 'created_at', 'total_rating', 'pos_rating_recv_count', 'neg_rating_recv_count', 'pos_rating_sent_count', 'neg_rating_sent_count');
if (! in_array($sortby, $validkeys)){
    $sortby = "total_rating";
}

$var="sortorder";
$sortorder = isset($_GET[$var]) ? $_GET[$var] : "ASC";
$validorders = array("ASC","DESC");
if (! in_array($sortorder, $validorders)){
    $sortorder = "ASC";
}

echo "OTC web of trust summary";

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

<h2>OTC web of trust</h2>

<p>[<a href="/">home</a>]</p>

<h3>Summary statistics on web of trust</h3>

<ul>
<?php
if ($db = new PDO('sqlite:./otc/RatingSystem.db')) {
   $query = $db->Query('SELECT count(*) as usercount, sum(total_rating) as ratingsum FROM users');
    if ($query == false) {
        echo "<li>No outstanding orders found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['usercount'] . " users in database, with a total of " . $entry['ratingsum'] . " net rating points.</li>\n";

    $query = $db->Query("SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM ratings WHERE rating > 0");
    if ($query == false) {
        echo "<li>No positive ratings found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['ratingcount'] . " positive ratings sent, for a total of " . $entry['ratingsum'] . " points.</li>\n";

    $query = $db->Query("SELECT count(*) as ratingcount, sum(rating) as ratingsum FROM ratings WHERE rating < 0");
    if ($query == false) {
        echo "<li>No negative ratings found</li>" . "\n";
    }
    $entry = $query->fetch(PDO::FETCH_BOTH);
    echo "<li>" . $entry['ratingcount'] . " negative ratings sent, for a total of " . $entry['ratingsum'] . " points.</li>\n";
}
?>
</ul>

<h3>List of users and ratings</h3>

<table class="ratingdisplay">
<tr>

<?php
$sortorders = array('id' => 'ASC', 'nick' => 'ASC', 'created_at' => 'ASC', 'total_rating' => 'ASC', 'pos_rating_recv_count' => 'ASC', 'neg_rating_recv_count' => 'ASC', 'pos_rating_sent_count' => 'ASC', 'neg_rating_sent_count' => 'ASC');
if ($sortorder == 'ASC') {
  $sortorders[$sortby] = 'DESC';
}
echo '  <th><a href="viewratings.php?sortby=id&sortorder=' . $sortorders['id'] . '">id</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=created_at&sortorder=' . $sortorders['nick'] . '">nick</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=created_at&sortorder=' . $sortorders['created_at'] . '">created at</a><br>(UTC)</th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=refreshed_at&sortorder=' . $sortorders['total_rating'] . '">total rating</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=buysell&sortorder=' . $sortorders['pos_rating_recv_count'] . '">number of positive ratings received</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=nick&sortorder=' . $sortorders['neg_rating_recv_count'] . '">number of negative ratings received</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=host&sortorder=' . $sortorders['pos_rating_sent_count'] . '">number of positive ratings sent</a></th>' . "\n";
echo '  <th><a href="viewratings.php?sortby=btcamount&sortorder=' . $sortorders['neg_rating_sent_count'] . '">number of negative ratings sent</a></th>' . "\n";
?>
</tr>

<?php

if ($db = new PDO('sqlite:./otc/RatingSystem.db')) {
   $query = $db->Query('SELECT * FROM users ORDER BY ' . $sortby . ' ' . $sortorder );
    if ($query == false) {
        echo "<tr><td>No users found</td></tr>" . "\n";
    } 
    else {
        $color = 1;
        //$resultrow = 0;
        //$results = $query->fetchAll(PDO::FETCH_BOTH);
        while ($entry = $query->fetch(PDO::FETCH_BOTH)) {
            if ($color % 2 == 1){
                echo '<tr class="odd">' . "\n"; 
            }
            else {
                echo '<tr class="even">' . "\n";
            }
            $color = $color + 1;
            echo '  <td>' . $entry['id'] . '</td>' . "\n";
            echo '  <td><a href="viewreceived.php?nick=' . $entry['nick'] . '&type=ANY">' . preg_replace('/>/', '&gt;', preg_replace('/</', '&lt;', $entry['nick'])) . '</a></td>' . "\n";
            echo '  <td>' . gmdate('Y-m-d|H:i:s', $entry['created_at']) . '</td>' . "\n";
            echo '  <td>' . $entry['total_rating'] . '</td>' . "\n";
            echo '  <td><a href="viewreceived.php?nick=' . $entry['nick'] . '&type=POS">' . $entry['pos_rating_recv_count'] . '</a></td>' . "\n";
            echo '  <td><a href="viewreceived.php?nick=' . $entry['nick'] . '&type=NEG">' . $entry['neg_rating_recv_count'] . '</a></td>' . "\n";
            echo '  <td><a href="viewreceived.php?nick=' . $entry['nick'] . '&type=POS">' . $entry['pos_rating_sent_count'] . '</a></td>' . "\n";
            echo '  <td><a href="viewreceived.php?nick=' . $entry['nick'] . '&type=NEG">' . $entry['neg_rating_sent_count'] . '</a></td>' . "\n";
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
