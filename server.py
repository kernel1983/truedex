import json
from urllib.parse import unquote

import tornado.web
import tornado.ioloop
import tornado.websocket

import space
import func

# WebSocket clients for real-time push
connected_clients = set()

func.load_all_zips()


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()


# === Debug Pages ===

class DebugBaseHandler(BaseHandler):
    def render_debug_page(self, template_name, **kwargs):
        self.render(f"debug/{template_name}", **kwargs)


class DebugOverviewHandler(DebugBaseHandler):
    def get(self):
        total_state_entries = sum(len(s) for s in space.states.values())
        total_events = sum(len(v) for v in space.events.values())
        total_txs = len(space.transactions)

        self.render_debug_page("overview.html",
            title="Overview",
            latest_block=space.latest_block_number,
            total_blocks=len(space.blocks),
            total_txs=total_txs,
            total_events=total_events,
            total_state_entries=total_state_entries
        )


class DebugBlocksHandler(DebugBaseHandler):
    def get(self):
        blocks = []
        for blk_num in sorted(space.blocks.keys(), reverse=True)[:100]:
            blk_hash = space.block_hashes.get(blk_num, None)
            blk_time = space.block_times.get(blk_num, None)
            tx_count = len(space.blocks.get(blk_num, []))
            evt_count = len(space.events.get(blk_num, []))
            hash_str = (str(blk_hash)[:16] + "...") if blk_hash else "None"
            time_str = str(blk_time) if blk_time else "None"
            blocks.append({
                "num": blk_num,
                "hash": hash_str,
                "time": time_str,
                "tx_count": tx_count,
                "evt_count": evt_count
            })
        self.render_debug_page("blocks.html", title="Blocks", blocks=blocks)


class DebugBlockHandler(DebugBaseHandler):
    def get(self, block_num):
        blk_num = int(block_num)
        blk_hash = space.block_hashes.get(blk_num, None)
        blk_time = space.block_times.get(blk_num, None)
        txs = space.blocks.get(blk_num, [])
        evts = space.events.get(blk_num, [])

        tx_list = []
        for tx in txs:
            tx_hash = tx[1] if isinstance(tx, tuple) else tx
            tx_data = space.transactions.get(tx_hash, {})
            tx_list.append({"hash": str(tx_hash), "data": json.dumps(tx_data, indent=2)})

        evt_list = []
        for evt in evts:
            evt_list.append({"event": str(evt.get("event")), "args": json.dumps(evt.get("args"), indent=2)})

        hash_str = str(blk_hash) if blk_hash else "None"
        time_str = str(blk_time) if blk_time else "None"

        self.render_debug_page("block.html",
            title="Block " + str(blk_num),
            blk_num=blk_num,
            blk_hash=hash_str,
            blk_time=time_str,
            txs=tx_list,
            evts=evt_list
        )


class DebugEventsHandler(DebugBaseHandler):
    def get(self):
        blocks = []
        for blk_num in sorted(space.events.keys(), reverse=True):
            evts = space.events[blk_num]
            evt_list = []
            for evt in evts:
                evt_list.append({"event": str(evt.get("event")), "args": json.dumps(evt.get("args"), indent=2)})
            blocks.append({"num": blk_num, "count": len(evts), "events": evt_list})
        self.render_debug_page("events.html", title="Events", blocks=blocks)


class DebugStateHandler(DebugBaseHandler):
    def get(self):
        prefix = self.get_argument("prefix", "")
        entries = []
        count = 0
        max_entries = 500
        for block_num in sorted(space.states.keys(), reverse=True):
            state = space.states[block_num]
            for key in sorted(state.keys()):
                if prefix and not key.startswith(prefix):
                    continue
                addr, value = state[key]
                entries.append({"key": str(key), "owner": str(addr), "value": str(value), "block_num": block_num})
                count += 1
                if count >= max_entries:
                    break
            if count >= max_entries:
                break
        self.render_debug_page("state.html",
            title="State Browser",
            prefix=prefix,
            entries=entries,
            count=count,
            max_entries=max_entries
        )


class DebugTransactionsHandler(DebugBaseHandler):
    def get(self):
        transactions = []
        for tx_hash, tx_data in sorted(space.transactions.items()):
            transactions.append({"hash": str(tx_hash), "data": json.dumps(tx_data, indent=2)})
        self.render_debug_page("transactions.html", title="Transactions", transactions=transactions)


class GetLatestStateAPIHandler(BaseHandler):
    def get(self):
        prefix = unquote(self.get_argument("prefix"))
        print(space.states)
        if "-" not in prefix:
            self.finish({"result": None})
            return
        idx = prefix.index("-")
        asset = prefix[:idx]
        rest = prefix[idx+1:]
        if ":" in rest:
            var, key = rest.split(":", 1)
        else:
            var = rest
            key = None
        value, owner = space.get(asset, var, None, key)
        self.finish({"result": value, "owner": owner})


class QueryRecentStateAPIHandler(BaseHandler):
    def get(self):
        prefix = self.get_argument("prefix")
        print(prefix)


class OrderbookAPIHandler(BaseHandler):
    def get(self):
        base = self.get_argument("base")
        quote = self.get_argument("quote")
        pair = f"{base}_{quote}"

        buys = []
        sells = []

        buy_start, _ = space.get("trade", f"{pair}_buy_start", 1)
        sell_start, _ = space.get("trade", f"{pair}_sell_start", 1)

        buy_id = buy_start
        while buy_id:
            buy, _ = space.get("trade", f"{pair}_buy", None, str(buy_id))
            if buy:
                buys.append({
                    "id": buy_id,
                    "owner": buy[0],
                    "base": str(buy[1]),
                    "quote": str(buy[2]),
                    "price": str(buy[3]),
                    "next": buy[4]
                })
                buy_id = buy[4]
            else:
                break

        sell_id = sell_start
        while sell_id:
            sell, _ = space.get("trade", f"{pair}_sell", None, str(sell_id))
            if sell:
                sells.append({
                    "id": sell_id,
                    "owner": sell[0],
                    "base": str(sell[1]),
                    "quote": str(sell[2]),
                    "price": str(sell[3]),
                    "next": sell[4]
                })
                sell_id = sell[4]
            else:
                break

        self.finish({"buys": buys, "sells": sells})


class HistoryAPIHandler(BaseHandler):
    def get(self):
        import math

        base = self.get_argument("base")
        quote = self.get_argument("quote")
        interval = self.get_argument("interval", "1s")
        limit = int(self.get_argument("limit", "100"))

        pair = f"{base}_{quote}"

        interval_seconds = {
            "1s": 1,
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "1d": 86400
        }
        if interval not in interval_seconds:
            interval = "1s"
        interval_sec = interval_seconds[interval]

        K = 10**18
        # Get quote token decimal for proper price display
        quote_decimal, _ = space.get(quote, 'decimal', 6)
        # Price stored as: total_quote * K // total_base
        # quote_amount = price * base_amount / K
        # To display price in quote token decimal: price / (K / 10^(18-decimal)) = price / 10^decimal
        price_divisor = 10**quote_decimal
        block_trades = {}

        for block_num in space.events:
            evts = space.events[block_num]
            for evt in evts:
                if evt["event"] in ["TradeLimitTake", "TradeMarketTake"]:
                    args = evt["args"]
                    if args[0] == pair:
                        if block_num not in block_trades:
                            block_trades[block_num] = []
                        block_trades[block_num].append({
                            "price": args[4],
                            "amount": args[3],
                            "buy_or_sell": args[1]
                        })

        block_candles = []
        for block_num in sorted(block_trades.keys()):
            trades = block_trades[block_num]
            prices = [t["price"] for t in trades if t["price"] > 0]
            if not prices:
                continue

            blk_time = space.block_times.get(block_num, block_num)
            candle = {
                "time": blk_time,
                "open": prices[0],
                "high": max(prices),
                "low": min(prices),
                "close": prices[-1],
                "volume": sum(t.get("amount", 0) for t in trades),
                "block_num": block_num
            }
            block_candles.append(candle)

        candles = {}
        for candle in block_candles:
            bucket = (candle["time"] // interval_sec) * interval_sec
            if bucket not in candles:
                candles[bucket] = {
                    "time": bucket,
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume": candle["volume"],
                    "block_nums": [candle["block_num"]],
                    "is_filled": False  # 真实交易蜡烛
                }
            else:
                candles[bucket]["high"] = max(candles[bucket]["high"], candle["high"])
                candles[bucket]["low"] = min(candles[bucket]["low"], candle["low"])
                candles[bucket]["close"] = candle["close"]
                candles[bucket]["volume"] += candle["volume"]
                candles[bucket]["block_nums"].append(candle["block_num"])
                candles[bucket]["is_filled"] = False  # 合并后仍是真实蜡烛

        sorted_times = sorted(candles.keys(), reverse=True)[:limit]
        result = [candles[t] for t in sorted_times]
        result.reverse()

        # Fill gaps with previous close price
        if result:
            filled = [result[0]]
            for candle in result[1:]:
                prev = filled[-1]
                expected = prev["time"] + interval_sec
                while expected < candle["time"]:
                    filled.append({
                        "time": expected,
                        "open": prev["close"],
                        "high": prev["close"],
                        "low": prev["close"],
                        "close": prev["close"],
                        "volume": 0,
                        "block_nums": [],
                        "is_filled": True  # 标记为补全的蜡烛
                    })
                    expected += interval_sec
                filled.append(candle)
            result = filled

            # Fill to current time
            import time
            now = int(time.time())
            now = (now // interval_sec) * interval_sec  # Align to interval boundary
            last_candle = result[-1]
            expected = last_candle["time"] + interval_sec
            while expected <= now:
                result.append({
                    "time": expected,
                    "open": last_candle["close"],
                    "high": last_candle["close"],
                    "low": last_candle["close"],
                    "close": last_candle["close"],
                    "volume": 0,
                    "block_nums": [],
                    "is_filled": True  # 标记为补全的蜡烛
                })
                last_candle = result[-1]
                expected += interval_sec

            # Apply limit after filling to current time
            result = result[-limit:]

        # 确保 open 承接前一个 close，让 K 线视觉连续
        if len(result) > 1:
            for i in range(1, len(result)):
                result[i]["open"] = result[i-1]["close"]

        for c in result:
            c["open"] = c["open"] / price_divisor
            c["high"] = c["high"] / price_divisor
            c["low"] = c["low"] / price_divisor
            c["close"] = c["close"] / price_divisor
            if not c.get("is_filled"):
                del c["block_nums"]
            # 真实交易的蜡烛保留 block_nums（如果有），补全的删除

        # 返回时包含 is_filled 标记
        self.finish({"candles": result})


class EventsAPIHandler(BaseHandler):
    def get(self):
        block = self.get_argument("block", None)

        all_events = []
        for block_num, evts in space.events.items():
            if block is None or block_num >= int(block):
                for evt in evts:
                    all_events.append({
                        "block": block_num,
                        "event": evt.get("event"),
                        "args": evt.get("args")
                    })

        self.finish({"events": all_events[-50:], "total": len(all_events)})


class IndexerAPIHandler(BaseHandler):
    def get(self):
        txhash = self.get_argument("txhash")
        print("[IndexerAPIHandler] GET txhash=" + txhash)
        self.finish({"result": []})

    def post(self):
        import tornado.escape
        try:
            data = tornado.escape.json_decode(self.request.body)
        except:
            self.set_status(400)
            self.finish({"error": "Invalid JSON"})
            return

        print("[IndexerAPIHandler] POST: " + str(data))

        try:
            info = data.get("info", {})
            args = data.get("args", [])
            sender = info.get("sender", "")
            func.set_sender(sender)
            func_name = info.get("name")
            slot = info.get("slot") or 0
            block_time = info.get("block_time")
            tx_index = info.get("tx_index", 0)
            txhash = info.get("txhash", "")

            block_number = space.nextblock(slot=slot if slot > 0 else None, timestamp=block_time)

            # 把 block_number 和 tx_index 放入 info
            info["block_number"] = block_number
            info["tx_index"] = tx_index

            if txhash:
                if block_number not in space.blocks:
                    space.blocks[block_number] = []
                space.blocks[block_number].append((tx_index, txhash))
                # 只存需要的字段，过滤掉 opcode
                filtered_info = {
                    "name": info.get("name"),
                    "block_time": info.get("block_time"),
                    "slot": info.get("slot"),
                    "sender": info.get("sender"),
                    "txhash": info.get("txhash"),
                    "block_number": info.get("block_number"),
                    "tx_index": info.get("tx_index"),
                }
                space.transactions[txhash] = {
                    "info": filtered_info,
                    "args": args
                }

            if func_name and func_name in func.namespace:
                call_args = {"p": "zen", "a": args, "f": func_name}
                call_args["f"] = func_name
                print("[IndexerAPIHandler] calling " + func_name + " with info=" + str(info) + ", args=" + str(call_args))
                wrapped = func.namespace[func_name]
                result = wrapped.f(info, call_args)
                print("[IndexerAPIHandler] result: " + str(result))

                # Broadcast new trade to WS clients BEFORE finish
                if func_name in ["trade_limit_order", "trade_market_order"]:
                    # Get the actual trade event from space.events
                    block_number = info.get("block_number")
                    if block_number and block_number in space.events:
                        for evt in space.events[block_number]:
                            if evt["event"] in ["TradeLimitTake", "TradeMarketTake"]:
                                evt_args = evt["args"]
                                if len(evt_args) >= 5:
                                    pair = evt_args[0]
                                    parts = pair.split("_")
                                    if len(parts) == 2:
                                        base, quote = parts
                                        quote_decimal, _ = space.get(quote, 'decimal', 6)
                                        base_decimal = 18  # BTC decimal

                                        trade_msg = {
                                            "type": "trade",
                                            "timestamp": info.get("block_time"),
                                            "price": evt_args[4] / (10**quote_decimal),
                                            "amount": evt_args[3] / (10**base_decimal),
                                            "side": evt_args[1],
                                            "pair": pair
                                        }
                                        broadcast(json.dumps(trade_msg))
                                break

                self.finish({"result": result})
            else:
                self.set_status(400)
                self.finish({"error": "Function " + str(func_name) + " not found"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.finish({"error": str(e)})


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        connected_clients.add(self)
        print(f"✅ WS client connected, total: {len(connected_clients)}")

    def on_close(self):
        connected_clients.discard(self)
        print(f"❌ WS client disconnected, total: {len(connected_clients)}")

    def check_origin(self, origin):
        return True  # Allow CORS in dev


def broadcast(message):
    """Push message to all connected WS clients"""
    to_remove = set()
    for client in connected_clients:
        try:
            client.write_message(message)
        except Exception as e:
            print(f"Broadcast error: {e}")
            to_remove.add(client)
    for c in to_remove:
        connected_clients.discard(c)


def start_server():
    app = tornado.web.Application([
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static/"}),
        (r"/debug/", DebugOverviewHandler),
        (r"/debug/blocks", DebugBlocksHandler),
        (r"/debug/block/(\d+)", DebugBlockHandler),
        (r"/debug/events", DebugEventsHandler),
        (r"/debug/state", DebugStateHandler),
        (r"/debug/transactions", DebugTransactionsHandler),
        (r"/", IndexerAPIHandler),
        (r"/api/get_latest_state", GetLatestStateAPIHandler),
        (r"/api/query_recent_state", QueryRecentStateAPIHandler),
        (r"/api/orderbook", OrderbookAPIHandler),
        (r"/api/history", HistoryAPIHandler),
        (r"/api/events", EventsAPIHandler),
        (r"/ws", WSHandler),
    ], template_path="templates", debug=True)
    app.listen(3000)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    print("http://127.0.0.1:3000")
    start_server()
