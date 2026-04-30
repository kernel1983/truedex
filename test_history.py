#!/usr/bin/env python3
"""Test HistoryAPIHandler with tornado.testing"""
import json
import time
import unittest

import space
import tornado.testing
import tornado.web

from server import *


def create_app():
    return tornado.web.Application([
        (r"/api/history", HistoryAPIHandler),
        (r"/api/orderbook", OrderbookAPIHandler),
        (r"/api/get_latest_state", GetLatestStateAPIHandler),
    ], debug=True)


class TestHistoryAPI(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return create_app()

    def setUp(self):
        super().setUp()
        space.events.clear()
        space.block_times.clear()
        space.states.clear()

    def test_fill_gaps(self):
        """Fill empty time buckets with previous close price"""
        pair = "BTC_USDC"
        base, quote = pair.split("_")
        base_time = int(time.time()) // 3600 * 3600

        # Hour 0: close=50
        space.block_times[100] = base_time
        space.events[100] = [
            {"event": "TradeLimitTake", "args": [pair, "buy", 0, 10**18, 50000000]},
        ]

        # Hour 2: close=53 (skip hour 1)
        space.block_times[101] = base_time + 7200
        space.events[101] = [
            {"event": "TradeLimitTake", "args": [pair, "buy", 0, 10**18, 53000000]},
        ]

        resp = self.fetch(f"/api/history?base={base}&quote={quote}&interval=1h&limit=5")
        data = json.loads(resp.body)
        candles = data['candles']
        print(f"\nFill gaps test ({len(candles)} candles):")
        for c in candles:
            print(f"  time={c['time']}, open={c['open']}, high={c['high']}, low={c['low']}, close={c['close']}, volume={c['volume']}")

        # Should have 3 candles: hour 0, 1 (filled), 2
        self.assertEqual(len(candles), 3)

        # Hour 0: actual data
        self.assertEqual(candles[0]['time'], base_time)
        self.assertEqual(candles[0]['close'], 50.0)

        # Hour 1: filled with previous close
        self.assertEqual(candles[1]['time'], base_time + 3600)
        self.assertEqual(candles[1]['close'], 50.0)  # filled with previous close
        self.assertEqual(candles[1]['open'], 50.0)
        self.assertEqual(candles[1]['high'], 50.0)
        self.assertEqual(candles[1]['low'], 50.0)
        self.assertEqual(candles[1]['volume'], 0)

        # Hour 2: actual data
        self.assertEqual(candles[2]['time'], base_time + 7200)
        self.assertEqual(candles[2]['close'], 53.0)

    def test_no_gaps(self):
        """No gaps when trades are consecutive"""
        pair = "BTC_USDC"
        base, quote = pair.split("_")
        base_time = int(time.time()) // 3600 * 3600

        for i in range(3):
            block = 100 + i
            space.block_times[block] = base_time + i * 3600
            space.events[block] = [
                {"event": "TradeLimitTake", "args": [pair, "buy", 0, 10**18, 50000000 + i*1000000]},
            ]

        resp = self.fetch(f"/api/history?base={base}&quote={quote}&interval=1h")
        data = json.loads(resp.body)
        candles = data['candles']
        print(f"\nNo gaps test ({len(candles)} candles)")
        self.assertEqual(len(candles), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
