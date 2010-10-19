<html>
<head><title>#bitcoin-otc guide</title></head>

<body>

<h2>Guide to safely using #bitcoin-otc</h2>

<p>#bitcoin-otc is merely an aggregator of outstanding supply and demand. All transactions that may occur are conducted directly between counterparties, without any participation or intermediation from #bitcoin-otc. As such, it is each individual's responsibility to conduct due diligence on their counterparties, and otherwise act in a prudent way to avoid falling prey to fraudulent users. Below are some guidelines that you should consider when engaging in OTC transactions.</p>

<h3>Risk of fraud</h3>
<p>When you trade OTC you engage in a transaction with people you possibly know nothing about. You may send your BTC to the person, and never get anything back. Or you may send your $currency to the person expecting BTC, and get nothing in return. This is a highly undesirable outcome for you, and you should do your best to guard against that. If you do not have a history of previous transactions with this person, or otherwise do not trust your counterparty, there are several mechanisms you can use to mitigate the risk of fraud:
<ul>
<li>You could choose a trustworthy third party to act as escrow. In this scheme, you send BTC to escrow party, your trading counterparty sends you $currency, you tell the escrow party to release the BTC over to your trading counterparty only when you have received $currency.</li>
<li>For a larger transaction, you can split up your trade into smaller chunks. So, e.g., instead of sending all 1000 btc at once to your counterparty and then waiting for payment, you could exchange it in chunks of 100 btc, so your maximum possible loss due to fraud is only 100 btc, rather than the whole 1000.</li>
</ul>
</p>

<h3>Notes on chargebacks</h3>

<p>When trading BTC for reversible methods (such as paypal or credit card transactions), beware of chargeback risk. It is strongly recommended to avoid PayPal or credit card transactions with persons of unknown reputation, since even with escrow, your counterparty may chargeback the PayPal funds after receiving the BTC.</p>

<p>One possible way to avoid these issues with PayPal is to use "personal gift" transactions which come out of PayPal or bank balance (rather than credit card). These transactions are not chargeback-able, and as a bonus, incur no fees. However, note that if your counterparty is using a stolen PayPal account, even these transactions may be reversed by PayPal once the real owner of the account files a complaint. So it's best to avoid PayPal when dealing with counterparties with no reputation.</p>

<h2>#bitcoin-otc user guide</h2>

<h3>Order entry</h3>
<ul>
<li>To enter orders, you must be <a href="http://freenode.net/faq.shtml#nicksetup">registered</a> with freenode, and have a <a href="http://freenode.net/faq.shtml#cloaks">cloak</a>. This is to prevent drive-by spam attacks on the order database, and to increase the trust level among the users. 
<li>To enter buy or sell orders, use the 'buy' and 'sell' commands with the bot. Bot's command string is ';;', so to enter a buy order, you might, for example, enter:
<pre>;;buy 1000 btc at 0.08 LRUSD</pre>
<li>To view your open orders (maximum 4 open orders per user) use the 'view' command
<li>To remove your open orders, use the 'remove' command. You may specify a particular open order to remove by providing an order ID.
<li>Open orders expire after a week, to avoid database cruft. To renew your outstanding orders, use the 'refresh' command to reset expiration date.
<li>To view the order book for a particular currency, use the 'book' command. E.g., you might run the following to see outstanding orders for LRUSD (LibertyReserve USD):
<pre>;;book lrusd</pre>
<li>If you have a web browser, best way to view the open order book is to visit <a href="vieworderbook.php">the online order book</a>.
</ul>

<h3>Trading</h3>

<p>There are no automatic systems set up to match buyers and sellers. The entire system is OTC, if you see a bid/ask you like, enter a matching order, and contact the counterparty directly on channel or in private message to set up the transaction. Issues to discuss may be: who bears the transaction fees? Who pays first? What escrow agent do we use that is mutually trusted? Remember, this is a direct negotiated transaction - so every detail is negotiable.</p>

<p>Once your trade is complete, don't forget to remove or update your outstanding open orders.</p>

</body>
</html>