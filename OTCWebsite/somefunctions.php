<?php

error_reporting(E_ALL & ~ E_NOTICE & ~E_WARNING);

try {
	$f = fopen("mtgox.json", "r");
	$goxtic = fread($f, 2048);
	fclose($f);
	$goxtic = json_decode($goxtic, true);
	$f = fopen("bitstamp.json", "r");
	$btsptic = fread($f, 2048);
	fclose($f);
	$btsptic = json_decode($btsptic, true);
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
	global $goxtic;
	global $btsptic;
	$indexedprice = $rawprice;
	try {
		if ( preg_match("/mtgox/", $rawprice) ){
			$indexedprice = preg_replace("/{mtgoxask}/", $goxtic['ask'], $indexedprice);
			$indexedprice = preg_replace("/{mtgoxbid}/", $goxtic['bid'], $indexedprice);
			$indexedprice = preg_replace("/{mtgoxlast}/", $goxtic['last'], $indexedprice);
			$indexedprice = preg_replace("/{mtgoxhigh}/", $goxtic['high'], $indexedprice);
			$indexedprice = preg_replace("/{mtgoxlow}/", $goxtic['low'], $indexedprice);
			$indexedprice = preg_replace("/{mtgoxavg}/", $goxtic['avg'], $indexedprice);
		}
		if (preg_match("/bitstamp/", $rawprice) ){
			$indexedprice = preg_replace("/{bitstampask}/", $btsptic['ask'], $indexedprice);
			$indexedprice = preg_replace("/{bitstampbid}/", $btsptic['bid'], $indexedprice);
			$indexedprice = preg_replace("/{bitstamplast}/", $btsptic['last'], $indexedprice);
			$indexedprice = preg_replace("/{bitstamphigh}/", $btsptic['high'], $indexedprice);
			$indexedprice = preg_replace("/{bitstamplow}/", $btsptic['low'], $indexedprice);
			$indexedprice = preg_replace("/{bitstampavg}/", $btsptic['avg'], $indexedprice);
		}
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