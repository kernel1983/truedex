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

    # def test_single_candle(self):
    #     """Single candle when trades in same time bucket"""
    #     pair = "BTC_USDC"
    #     base, quote = pair.split("_")
    #     base_time = int(time.time()) // 3600 * 3600

    #     space.block_times[100] = base_time
    #     space.events[100] = [
    #         {"event": "TradeLimitTake", "args": [pair, "buy", 0, 10**18, 50000000]},
    #         {"event": "TradeLimitTake", "args": [pair, "sell", 0, 2*10**18, 52000000]},
    #     ]

    #     resp = self.fetch(f"/api/history?base={base}&quote={quote}&interval=1h")
    #     data = json.loads(resp.body)
    #     print(f"Single candle: {json.dumps(data['candles'], indent=2)}")
    #     self.assertEqual(len(data['candles']), 1)

    def test_multiple_candles(self):
        """Multiple candles for different time buckets"""
        pair = "BTC_USDC"
        base, quote = pair.split("_")
        base_time = int(time.time()) // 3600 * 3600

        for i in range(7):
            block = 100 + i
            space.block_times[block] = base_time + i * 1800
            space.events[block] = [
                {"event": "TradeLimitTake", "args": [pair, "buy", 0, 10**18, 50000000 + i*1000000]},
            ]

        resp = self.fetch(f"/api/history?base={base}&quote={quote}&interval=1h")
        data = json.loads(resp.body)
        print(f"Multiple candles ({len(data['candles'])}): {json.dumps(data['candles'], indent=2)}")
        self.assertEqual(len(data['candles']), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
