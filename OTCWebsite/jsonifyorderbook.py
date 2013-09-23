import json
import sqlite3

class JsonifyOrderBook:
    def __init__(self, orderbook_db_path, json_path):
        self.json_path = json_path
        self.db = sqlite3.connect(orderbook_db_path)
        self.db.text_factory = str

    def run(self):
        i = True
        f = open(self.json_path, 'w')
        f.write('[')
        cursor = self.db.cursor()
        cursor.execute("""SELECT id,created_at,refreshed_at,buysell,nick,amount,thing,price,otherthing,notes FROM orders""")
        for row in cursor:
            d = dict(zip(['id','created_at','refreshed_at','buysell','nick','amount','thing','price','otherthing','notes'],row))
            if not i:
                f.write(',')
            try:
                f.write(json.dumps(d, encoding='latin1'))
            except:
                pass # if it's not decodable, skip it without further ado.
            i = False
        f.write(']')

if __name__ == '__main__':
    job = JsonifyOrderBook( 'otc/OTCOrderBook.db', 'orderbook.json')
    job.run()
