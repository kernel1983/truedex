import json
from urllib.parse import unquote

import tornado.web
import tornado.ioloop

import space
import func

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
    def render_debug_page(self, title, content):
        html = (
            '<!DOCTYPE html>\n'
            '<html>\n<head>\n'
            '    <meta charset="utf-8">\n'
            '    <title>Debug: ' + title + '</title>\n'
            '    <style>\n'
            '        body { font-family: monospace; margin: 20px; background: #f5f5f5; }\n'
            '        h1, h2, h3 { color: #333; }\n'
            '        table { border-collapse: collapse; width: 100%; background: white; margin: 10px 0; }\n'
            '        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n'
            '        th { background: #4CAF50; color: white; }\n'
            '        tr:nth-child(even) { background: #f9f9f9; }\n'
            '        tr:hover { background: #e0e0e0; }\n'
            '        a { color: #0066cc; text-decoration: none; }\n'
            '        a:hover { text-decoration: underline; }\n'
            '        .stats { background: white; padding: 15px; border-radius: 5px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n'
            '        .collapsible { cursor: pointer; background: #f0f0f0; }\n'
            '        .content { display: none; }\n'
            '        input[type=text] { padding: 5px; width: 300px; margin: 5px; }\n'
            '        button { padding: 5px 10px; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 3px; }\n'
            '        button:hover { background: #45a049; }\n'
            '        pre { white-space: pre-wrap; word-wrap: break-word; }\n'
            '    </style>\n'
            '    <script>\n'
            '        function toggle(id) {\n'
            '            const el = document.getElementById(id);\n'
            '            el.style.display = el.style.display === "none" ? "block" : "none";\n'
            '        }\n'
            '        function filterTable(inputId, tableId) {\n'
            '            const input = document.getElementById(inputId);\n'
            '            const filter = input.value.toUpperCase();\n'
            '            const table = document.getElementById(tableId);\n'
            '            const trs = table.getElementsByTagName("tr");\n'
            '            for (let i = 1; i < trs.length; i++) {\n'
            '                const txt = trs[i].textContent || trs[i].innerText;\n'
            '                trs[i].style.display = txt.toUpperCase().includes(filter) ? "" : "none";\n'
            '            }\n'
            '        }\n'
            '    </script>\n'
            '</head>\n<body>\n'
            '    <h1>Debug: ' + title + '</h1>\n'
            '    <p><a href="/debug/">Back to Overview</a></p>\n'
            + content +
            '</body>\n</html>\n'
        )
        self.finish(html)


class DebugOverviewHandler(DebugBaseHandler):
    def get(self):
        total_state_entries = sum(len(s) for s in space.states.values())
        total_events = sum(len(v) for v in space.events.values())
        total_txs = len(space.transactions)

        content = (
            '<div class="stats">\n'
            '    <h3>Statistics</h3>\n'
            '    <p><b>Latest Block:</b> ' + str(space.latest_block_number) + '</p>\n'
            '    <p><b>Total Blocks:</b> ' + str(len(space.blocks)) + '</p>\n'
            '    <p><b>Total Transactions:</b> ' + str(total_txs) + '</p>\n'
            '    <p><b>Total Events:</b> ' + str(total_events) + '</p>\n'
            '    <p><b>Total State Entries:</b> ' + str(total_state_entries) + '</p>\n'
            '</div>\n'
            '<h3>Quick Links</h3>\n'
            '<ul>\n'
            '    <li><a href="/debug/blocks">Blocks List</a></li>\n'
            '    <li><a href="/debug/events">Events Browser</a></li>\n'
            '    <li><a href="/debug/state">State Browser</a></li>\n'
            '    <li><a href="/debug/transactions">Transactions List</a></li>\n'
            '</ul>\n'
        )
        self.render_debug_page("Overview", content)


class DebugBlocksHandler(DebugBaseHandler):
    def get(self):
        rows = ""
        for blk_num in sorted(space.blocks.keys(), reverse=True)[:100]:
            blk_hash = space.block_hashes.get(blk_num, None)
            blk_time = space.block_times.get(blk_num, None)
            tx_count = len(space.blocks.get(blk_num, []))
            evt_count = len(space.events.get(blk_num, []))
            hash_str = (str(blk_hash)[:16] + "...") if blk_hash else "None"
            time_str = str(blk_time) if blk_time else "None"
            rows += (
                '<tr>\n'
                '    <td><a href="/debug/block/' + str(blk_num) + '">' + str(blk_num) + '</a></td>\n'
                '    <td>' + hash_str + '</td>\n'
                '    <td>' + time_str + '</td>\n'
                '    <td>' + str(tx_count) + '</td>\n'
                '    <td>' + str(evt_count) + '</td>\n'
                '</tr>\n'
            )
        content = (
            '<input type="text" id="filterInput" onkeyup="filterTable(\'filterInput\', \'blocksTable\')" placeholder="Filter blocks...">\n'
            '<table id="blocksTable">\n'
            '    <tr><th>Block #</th><th>Hash</th><th>Time</th><th>Tx Count</th><th>Event Count</th></tr>\n'
            + rows +
            '</table>\n'
        )
        self.render_debug_page("Blocks", content)


class DebugBlockHandler(DebugBaseHandler):
    def get(self, block_num):
        blk_num = int(block_num)
        blk_hash = space.block_hashes.get(blk_num, None)
        blk_time = space.block_times.get(blk_num, None)
        txs = space.blocks.get(blk_num, [])
        evts = space.events.get(blk_num, [])

        tx_rows = ""
        for tx in txs:
            tx_hash = tx[1] if isinstance(tx, tuple) else tx
            tx_data = space.transactions.get(tx_hash, {})
            tx_rows += "<tr><td>" + str(tx_hash) + "</td><td><pre>" + json.dumps(tx_data, indent=2) + "</pre></td></tr>\n"

        evt_rows = ""
        for evt in evts:
            evt_rows += "<tr><td>" + str(evt.get("event")) + "</td><td><pre>" + json.dumps(evt.get("args"), indent=2) + "</pre></td></tr>\n"

        hash_str = str(blk_hash) if blk_hash else "None"
        time_str = str(blk_time) if blk_time else "None"

        content = (
            "<h3>Block #" + str(blk_num) + "</h3>\n"
            "<p><b>Hash:</b> " + hash_str + "</p>\n"
            "<p><b>Time:</b> " + time_str + "</p>\n"
            "<h4>Transactions (" + str(len(txs)) + ")</h4>\n"
            "<table><tr><th>Tx Hash</th><th>Data</th></tr>" + tx_rows + "</table>\n"
            "<h4>Events (" + str(len(evts)) + ")</h4>\n"
            "<table><tr><th>Event</th><th>Args</th></tr>" + evt_rows + "</table>\n"
        )
        self.render_debug_page("Block " + str(blk_num), content)


class DebugEventsHandler(DebugBaseHandler):
    def get(self):
        rows = ""
        for blk_num in sorted(space.events.keys(), reverse=True):
            evts = space.events[blk_num]
            rows += (
                '<tr class="collapsible" onclick="toggle(\'evts_' + str(blk_num) + '\')">\n'
                '    <td><b>Block ' + str(blk_num) + '</b></td>\n'
                '    <td>' + str(len(evts)) + ' events</td>\n'
                '</tr>\n'
                '<tr id="evts_' + str(blk_num) + '" class="content">\n'
                '    <td colspan="2">\n'
                '        <table>\n'
                '            <tr><th>Event</th><th>Args</th></tr>\n'
            )
            for evt in evts:
                rows += "<tr><td>" + str(evt.get("event")) + "</td><td><pre>" + json.dumps(evt.get("args"), indent=2) + "</pre></td></tr>\n"
            rows += '        </table></td></tr>\n'

        content = (
            '<table>\n'
            '    <tr><th>Block</th><th>Event Count</th></tr>\n'
            + rows +
            '</table>\n'
        )
        self.render_debug_page("Events", content)


class DebugStateHandler(DebugBaseHandler):
    def get(self):
        prefix = self.get_argument("prefix", "")
        rows = ""
        count = 0
        max_entries = 500
        for block_num in sorted(space.states.keys(), reverse=True):
            state = space.states[block_num]
            for key in sorted(state.keys()):
                if prefix and not key.startswith(prefix):
                    continue
                addr, value = state[key]
                rows += "<tr><td>" + str(key) + "</td><td>" + str(addr) + "</td><td>" + str(value) + " (block " + str(block_num) + ")</td></tr>\n"
                count += 1
                if count >= max_entries:
                    break
            if count >= max_entries:
                break
        content = (
            '<form>\n'
            '    <label>Filter by prefix: <input type="text" name="prefix" value="' + prefix + '"></label>\n'
            '    <button type="submit">Filter</button>\n'
            '</form>\n'
            '<p>Showing ' + str(count) + ' entries (max ' + str(max_entries) + ').</p>\n'
            '<table>\n'
            '    <tr><th>Key</th><th>Owner</th><th>Value</th></tr>\n'
            + rows +
            '</table>\n'
        )
        self.render_debug_page("State Browser", content)


class DebugTransactionsHandler(DebugBaseHandler):
    def get(self):
        rows = ""
        for tx_hash, tx_data in sorted(space.transactions.items()):
            rows += "<tr><td>" + str(tx_hash) + "</td><td><pre>" + json.dumps(tx_data, indent=2) + "</pre></td></tr>\n"
        content = (
            '<table>\n'
            '    <tr><th>Tx Hash</th><th>Data</th></tr>\n'
            + rows +
            '</table>\n'
        )
        self.render_debug_page("Transactions", content)


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
                    "block_nums": [candle["block_num"]]
                }
            else:
                candles[bucket]["high"] = max(candles[bucket]["high"], candle["high"])
                candles[bucket]["low"] = min(candles[bucket]["low"], candle["low"])
                candles[bucket]["close"] = candle["close"]
                candles[bucket]["volume"] += candle["volume"]
                candles[bucket]["block_nums"].append(candle["block_num"])

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
                        "block_nums": []
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
                    "block_nums": []
                })
                last_candle = result[-1]
                expected += interval_sec

            # Apply limit after filling to current time
            result = result[-limit:]

        for c in result:
            c["open"] = c["open"] / price_divisor
            c["high"] = c["high"] / price_divisor
            c["low"] = c["low"] / price_divisor
            c["close"] = c["close"] / price_divisor
            del c["block_nums"]

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
                self.finish({"result": result})
            else:
                self.set_status(400)
                self.finish({"error": "Function " + str(func_name) + " not found"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.set_status(500)
            self.finish({"error": str(e)})


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
    ], debug=True)
    app.listen(3000)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    print("http://127.0.0.1:3000")
    start_server()
