#!/usr/bin/env python

import time
import logging
from binance.lib.utils import config_logging
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

config_logging(logging, logging.DEBUG)


def message_handler(message):
    print(message)


my_client = UMFuturesWebsocketClient()
my_client.start()

my_client.kline(symbol="btcusdt", id=1, interval="1m", callback=message_handler)

time.sleep(5)

my_client.kline(symbol="bnbusdt", id=2, interval="3m", callback=message_handler)

time.sleep(10)

logging.debug("closing ws connection")
my_client.stop()
