import threading
import time

from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceOrderException, BinanceAPIException
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor
from decimal import Decimal as D, ROUND_DOWN, ROUND_UP
import decimal

with open("api.txt", "r") as file:
    api_key = file.readline().strip()
    api_secret = file.readline().strip()

client = Client(api_key, api_secret)
# client.API_URL = 'https://testnet.binance.vision/api'
# print(client.API_URL)

class PriceFetcher(threading.Thread):
    def __init__(self, coin_pair, label):
        threading.Thread.__init__(self)
        self.running = True
        self.final_closure = False
        self.coin_pair = coin_pair.upper()
        self.label = label
        self.bsm = BinanceSocketManager(client)
        self.conn_key = self.bsm.start_symbol_ticker_socket(self.coin_pair, self.price_parser)

    def price_parser(self, msg):
        if not self.running:
            self.bsm.stop_socket(self.conn_key)
            self.bsm.close()
            if self.final_closure:
                reactor.stop()
        if msg['e'] != 'error':
            self.label.text = str(msg['c'])

    def run(self):
        self.bsm.start()


class TrailingBot(threading.Thread):
    def __init__(self, trail_type, symbol, amount, dist, status_label, live_price):
        threading.Thread.__init__(self)
        self.running = True
        self.trail_type = trail_type
        self.symbol = symbol
        self.amount = float(amount)
        self.dist = float(dist)
        self.status_label = status_label
        status_label.text = 'running'
        self.live_price = live_price

    def run(self):
        last_price = float(self.live_price.text)
        while self.running:
            time.sleep(0.5)
            current_price = float(self.live_price.text)
            diff = current_price - last_price
            if abs(diff / last_price) >= self.dist / 100.0:
                self.running = False
                self.execute_trade()
            if self.trail_type == 'sell' and current_price > last_price:
                last_price = current_price
            elif self.trail_type == 'buy' and current_price < last_price:
                last_price = current_price
        self.status_label.text = 'idle'

    def execute_trade(self):
        try:
            info = client.get_symbol_info(symbol=self.live_price.text)
            minimum = float(info['filters'][2]['minQty'])  # 'minQty'
            quantity = D.from_float(self.amount).quantize(D(str(minimum)))
            if self.trail_type == 'sell':
                client.create_order(symbol=self.symbol,
                                    side=SIDE_SELL,
                                    type=ORDER_TYPE_MARKET,
                                    quantity=quantity)
            if self.trail_type == 'buy':
                client.create_order(symbol=self.symbol,
                                    side=SIDE_BUY,
                                    type=ORDER_TYPE_MARKET,
                                    quantity=quantity)

        except BinanceAPIException as e:
            print(e)
        except BinanceOrderException as e:
            print(e)


def get_balance(asset):
    return client.get_asset_balance(asset=asset.upper())['free']
