<?php
# Thanks to http://stackoverflow.com/a/2770280
# for the nice snippet.
function jsonOutput($query)
{
    echo json_encode($query);
}

function jsonlink() {
    if ($_SERVER["QUERY_STRING"] != "")
        $sep = '&';
    else
        $sep = '?';
    echo $_SERVER["REQUEST_URI"] . $sep . "outformat=json";
}
?>
