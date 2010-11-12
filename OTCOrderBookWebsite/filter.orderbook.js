$(window).load(function() {
	$(window).bind( 'hashchange', function(e) { loadfilters();});

	if (!$("select#filter_type").length)
		$("table.orderbookdisplay tr").children("th.type")
			.append("<br><br><select id='filter_type'><option></option><option value='BUY'>BUY</option><option value='SELL'>SELL</option></select>");

	var pricemax = 0;
	$("table.orderbookdisplay tr").children("td.price").each(function() {
		if (parseFloat($(this).text()) > pricemax) pricemax = parseFloat($(this).text());
	});
	if (!$("select#filter_pricemin").length)
		$("table.orderbookdisplay tr").children("th.price")
			.append("<br><span style='white-space:nowrap;'>min:<select id='filter_pricemin'><option></option></select></span>")
			.append("<br><span style='white-space:nowrap;'>max:<select id='filter_pricemax'><option></option></select></span>");
	for (x=0;x<=pricemax;) {
		$("select#filter_pricemin").append("<option value='"+x.toFixed(2)+"'>"+x.toFixed(2)+"</option>");
		$("select#filter_pricemax").append("<option value='"+x.toFixed(2)+"'>"+x.toFixed(2)+"</option>");
		if (x.toFixed(2) < 1) x=x+0.01;
		else if (x.toFixed(2) < 10) x=x+0.1;
		else if (x.toFixed(2) < 100) x++;
		else if (x.toFixed(2) < 1000) x=x+10;
		else if (x.toFixed(2) < 10000) x=x+100;
		else if (x.toFixed(2) < 100000) x=x+1000;
		else x=x+10000;
	}

	if (!$("select#filter_currency").length)
		$("table.orderbookdisplay tr").children("th.currency")
			.append("<br><br><select id='filter_currency'><option></option><option value='EUR'>EUR</option><option value='LREUR'>LREUR</option><option value='LRUSD'>LRUSD</option><option value='MBEUR'>MBEUR</option><option value='MBUSD'>MBUSD</option><option value='MONEYPAK'>MONEYPAK</option><option value='MTGUSD'>MTGUSD</option><option value='PPEUR'>PPEUR</option><option value='PPUSD'>PPUSD</option><option value='PXGAU'>PXGAU</option><option value='USD'>USD</option></select>");

	$("select#filter_type").click(function() { applyfilter(); }).keyup(function() { $("select#filter_type").click(); });
	$("select#filter_pricemin").click(function() { applyfilter("pricemin"); }).keyup(function() { $("select#filter_pricemin").click(); });
	$("select#filter_pricemax").click(function() { applyfilter("pricemax"); }).keyup(function() { $("select#filter_pricemax").click(); });
	$("select#filter_currency").click(function() { applyfilter(); }).keyup(function() { $("select#filter_currency").click(); });
	loadfilters();
});

function applyfilter(w) {
	var filterval = "";
	$("table.orderbookdisplay tr").next().each(function(index) {
		$(this).show();
		if ($("select#filter_type").val() != "") {
			$("th a").fragment("filter_type="+$("select#filter_type").val());
			filterval = $(this).children("td.type").text();
			if (filterval.toUpperCase() != $("select#filter_type").val().toUpperCase()) $(this).hide();
		}
		else $("th a").fragment("filter_type");
		if ($("select#filter_pricemin").val() != "" || $("select#filter_pricemax").val() != "") {
			if ($("select#filter_pricemin").val() != "") $("th a").fragment("filter_pricemin="+$("select#filter_pricemin").val());
			else $("th a").fragment("filter_pricemin");
			if ($("select#filter_pricemax").val() != "")  $("th a").fragment("filter_pricemax="+$("select#filter_pricemax").val());
			else $("th a").fragment("filter_pricemax");
			filterval = $(this).children("td.price").text();
			var filter_pricemin = ($("select#filter_pricemin").val() == "") ? 0 : parseFloat($("select#filter_pricemin").val());
			var filter_pricemax = ($("select#filter_pricemax").val() == "") ? Infinity : parseFloat($("select#filter_pricemax").val());
			if (w == "pricemin" && filter_pricemax < filter_pricemin) $("select#filter_pricemax").val(filter_pricemin);
			else if (w == "pricemax" && filter_pricemin > filter_pricemax) $("select#filter_pricemin").val(filter_pricemax);
			if (parseFloat(filterval) < filter_pricemin || parseFloat(filterval) > filter_pricemax) $(this).hide();
		}
		if ($("select#filter_currency").val() != "") {
			$("th a").fragment("filter_currency="+$("select#filter_currency").val());
			filterval = $(this).children("td.currency").text();
			if (filterval == "PGAU") filterval = "PXGAU";
			if (filterval.toUpperCase() != $("select#filter_currency").val().toUpperCase()) $(this).hide();
		}
		else $("th a").fragment("filter_currency");
	});
}

function loadfilters() {
	var filtered = false;
	var filters = $.deparam.fragment();
	for (var filter in filters) {
		filtered = true;
		if (filter == "filter_type") $("select#filter_type").val(filters[filter]);
		if (filter == "filter_pricemin") $("select#filter_pricemin").val(filters[filter]);
		if (filter == "filter_pricemax") $("select#filter_pricemax").val(filters[filter]);
		if (filter == "filter_currency") $("select#filter_currency").val(filters[filter]);
	}
	if (filtered) applyfilter();
}