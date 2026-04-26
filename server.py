import tornado.web
import tornado.ioloop
import json

import space
import func

func.load_all_zips()
# GLOBAL_FUNCTIONS = func.namespace


class GetLatestStateAPIHandler(tornado.web.RequestHandler):
    def get(self):
        from urllib.parse import unquote
        prefix = unquote(self.get_argument('prefix'))
        if '-' not in prefix:
            self.finish({'result': None})
            return
        idx = prefix.index('-')
        asset = prefix[:idx]
        rest = prefix[idx+1:]
        if ':' in rest:
            var, key = rest.split(':', 1)
        else:
            var = rest
            key = None
        value, owner = space.get(asset, var, None, key)
        self.finish({'result': value, 'owner': owner})


class QueryRecentStateAPIHandler(tornado.web.RequestHandler):
    def get(self):
        prefix = self.get_argument('prefix')
        print(prefix)


class OrderbookAPIHandler(tornado.web.RequestHandler):
    def get(self):
        base = self.get_argument('base')
        quote = self.get_argument('quote')
        pair = f'{base}_{quote}'
        
        buys = []
        sells = []
        
        buy_start, _ = space.get('trade', f'{pair}_buy_start', 1)
        sell_start, _ = space.get('trade', f'{pair}_sell_start', 1)
        
        buy_id = buy_start
        while buy_id:
            buy, _ = space.get('trade', f'{pair}_buy', None, str(buy_id))
            if buy:
                buys.append({
                    'id': buy_id,
                    'owner': buy[0],
                    'base': str(buy[1]),
                    'quote': str(buy[2]),
                    'price': str(buy[3]),
                    'next': buy[4]
                })
                buy_id = buy[4]
            else:
                break
        
        sell_id = sell_start
        while sell_id:
            sell, _ = space.get('trade', f'{pair}_sell', None, str(sell_id))
            if sell:
                sells.append({
                    'id': sell_id,
                    'owner': sell[0],
                    'base': str(sell[1]),
                    'quote': str(sell[2]),
                    'price': str(sell[3]),
                    'next': sell[4]
                })
                sell_id = sell[4]
            else:
                break
        
        self.finish({'buys': buys, 'sells': sells, 'pair': pair})


class HistoryAPIHandler(tornado.web.RequestHandler):
    def get(self):
        base = self.get_argument('base')
        quote = self.get_argument('quote')
        pair = f'{base}_{quote}'
        
        start_block = int(self.get_argument('start_block', '0'))
        end_block = int(self.get_argument('end_block', str(space.latest_block_number)))

        trades = []
        for block_num in sorted(space.events.keys()):
            if block_num < start_block or block_num > end_block:
                continue
            for evt in space.events[block_num]:
                if evt['event'] in ('TradeOrderTake', 'TradeOrderMake') and pair in evt['args']:
                    event_data = {
                        'block': block_num,
                        'event': evt['event'],
                        'pair': evt['args'][0],
                        'side': evt['args'][1],
                        'address': evt['args'][2],
                        'amount': str(evt['args'][3]),
                        'price': str(evt['args'][4]),
                    }
                    trades.append(event_data)
        
        self.finish({
            'trades': trades,
            'pair': pair,
            'latest_block': space.latest_block_number
        })


class EventsAPIHandler(tornado.web.RequestHandler):
    def get(self):
        txhash = self.get_argument('txhash', None)
        limit = int(self.get_argument('limit', '100'))

        all_events = []
        for block_num in sorted(space.events.keys()):
            for evt in space.events[block_num]:
                all_events.append({'block': block_num, **evt})

        if txhash:
            all_events = [e for e in all_events if e.get('txhash') == txhash]

        all_events = all_events[-limit:]
        self.finish({'events': all_events, 'total': len(all_events)})


class IndexerAPIHandler(tornado.web.RequestHandler):
    def get(self):
        txhash = self.get_argument('txhash')
        print(f"[IndexerAPIHandler] GET txhash={txhash}")
        self.finish({'result': []})

    def post(self):
        import tornado.escape
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.finish({'error': 'Invalid JSON'})
            return

        print(f"[IndexerAPIHandler] POST: {data}")

        try:
            info = data.get('info', {})
            args = data.get('args', [])
            sender = info.get('sender', '')
            func.set_sender(sender)
            func_name = info.get('name')
            if func_name and func_name in func.namespace:
                call_args = {'p': 'zen', 'a': args, 'f': func_name}
                print(f"[IndexerAPIHandler] calling {func_name} with info={info}, args={call_args}")
                wrapped = func.namespace[func_name]
                result = wrapped.f(info, call_args)
                print(f"[IndexerAPIHandler] result: {result}")
                self.finish({'result': result})
            else:
                self.set_status(400)
                self.finish({'error': f'Function {func_name} not found'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.finish({'error': str(e)})


def start_server():
    space._init_block_mode()
    app = tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/'}),
        (r"/", IndexerAPIHandler),
        (r'/api/get_latest_state', GetLatestStateAPIHandler),
        (r'/api/query_recent_state', QueryRecentStateAPIHandler),
        (r'/api/orderbook', OrderbookAPIHandler),
        (r'/api/history', HistoryAPIHandler),
        (r'/api/events', EventsAPIHandler),
    ], debug=True)
    app.listen(3000)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    print('http://127.0.0.1:3000')
    start_server()