<?php
# Thanks to http://code-slim-jim.blogspot.com/2011/07/php-sqlite-to-json-converter-page.html
# for the nice snippet.
function jsonOutput($query)
{
    header('Content-type: application/json');
    $ofirst = true;
    print "[\n";
    foreach ($query as $row)
    {
        if($ofirst) $ofirst = false;
        else       print ",\n";

        $first = true;
        print "{";
        foreach ($row as $key => $value)
        {
            if($first) $first = false;
            else       print ",";
            if(is_numeric($value))
                print '"' . $key . '": ' . $value;
            else
                print '"' . $key . '": "' . $value . '"';
        }
        print "}";
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
