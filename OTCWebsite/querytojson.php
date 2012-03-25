<?php
# Thanks to http://code-slim-jim.blogspot.com/2011/07/php-sqlite-to-json-converter-page.html
# for the nice snippet.
# Thanks to graingert for pointing out that json_encode would eliminate a lot of code and
# produce actually correct json (escape control chars, etc.)
function jsonOutput($query)
{
    header('Content-type: application/json');
    $ofirst = true;
    print "[\n";
    foreach ($query as $row)
    {
        if($ofirst) $ofirst = false;
        else       print ",\n";
        
        $rowjs = json_encode($row);
        print $rowjs;
    }
    print "\n]\n";
}

function jsonlink() {
    if ($_SERVER["QUERY_STRING"] != "")
        $sep = '&';
    else
        $sep = '?';
    echo $_SERVER["REQUEST_URI"] . $sep . "outformat=json";
}
?>
