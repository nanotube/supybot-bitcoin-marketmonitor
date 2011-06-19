<?php

error_reporting(E_ALL & ~ E_NOTICE & ~E_WARNING);

try {
	$f = fopen("mtgox.json", "r");
	$ticker = fread($f, 1024);
	fclose($f);
	$ticker = json_decode($ticker, true);
	$ticker = $ticker['ticker'];
	$f = fopen("exchangerates.json", "r");
	$rates = fread($f, 4096);
	fclose($f);
	$rates = json_decode($rates, true);
} catch (Exception $e) {
}
function get_currency_conversion($rawprice){
	if (!preg_match("/{(...) in (...)}/i", $rawprice, $matches)){
	   return $rawprice;
	}
	$googlerate = query_google_rate($matches[1], $matches[2]);
	$indexedprice = preg_replace("/{... in ...}/i", $googlerate, $rawprice);
	return($indexedprice);
}

//~ function query_google_rate($cur1, $cur2){
	//~ $f = fopen("http://www.google.com/ig/calculator?hl=en&q=1" . $cur1 . "=?" . $cur2, "r");
	//~ $result = fread($f, 1024);
	//~ fclose($f);
	//~ $result	= preg_replace("/(\w+):/", "\"\\1\":", $result); //missing quotes in google json
	//~ $googlerate = json_decode($result, true);
	//~ if($googlerate['error'] != ""){
		//~ throw new Exception('google error');
	//~ }
	//~ $googlerate = explode(" ", $googlerate['rhs']);
	//~ $googlerate = $googlerate[0];
	//~ return($googlerate);
//~ }

function query_google_rate($cur1, $cur2){
	global $rates;
	$conv = '{' . strtolower($cur1) . ' in ' . strtolower($cur2) . '}';
	$rate = $rates[$conv];
	return($rate);
}

function doNothing() { return(true); }

function index_prices($rawprice){
	global $ticker;
	try {
		$indexedprice = preg_replace("/{mtgoxask}/", $ticker['sell'], $rawprice);
		$indexedprice = preg_replace("/{mtgoxbid}/", $ticker['buy'], $indexedprice);
		$indexedprice = preg_replace("/{mtgoxlast}/", $ticker['last'], $indexedprice);
		$indexedprice = get_currency_conversion($indexedprice);
		$code = 'set_error_handler("doNothing");return(' . $indexedprice . ');restore_error_handler();';
		ob_start();
		$indexedprice = eval($code);
		ob_clean();
		if ( $indexedprice === false ) {
			return($rawprice);
		}
		return($indexedprice);
	} catch (Exception $e) {
	  	return($rawprice);
	}
}
?>