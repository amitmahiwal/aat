import numpy as np
import string
from datetime import datetime
from random import choice, randint
from ..exchange import Exchange
from ...core import Instrument, OrderBook, Data
from ...config import Side, DataType


def _getName(n=1):
    columns = [''.join(np.random.choice(list(string.ascii_uppercase), choice((1, 2, 3, 4)))) + '.' + ''.join(np.random.choice(list(string.ascii_uppercase), choice((1, 2)))) for _ in range(n)]
    return columns


class SyntheticExchange(Exchange):
    def __init__(self, trading_engine=None):
        self._exchange_type = 'synthetic'

    def _seed(self, symbols=None):
        self._instruments = {symbol: Instrument(symbol) for symbol in symbols or _getName(1)}
        self._orderbooks = {symbol: OrderBook(i) for symbol, i in self._instruments.items()}
        self._seedOrders()

    def _seedOrders(self):
        for symbol, orderbook in self._orderbooks.items():
            x = .5
            while x < 10.0:
                side = Side.BUY if x <= 5 else Side.SELL
                orderbook.add(Data(id=1,
                                timestamp=datetime.now().timestamp(),
                                volume=1.0,
                                price=x,
                                side=side,
                                type=DataType.ORDER,
                                instrument=self._instruments[symbol],
                                exchange=self._exchange_type))
                x += .5

    def _testOrdersSample(self, count=5):
        for symbol, orderbook in self._orderbooks.items():
            data = Data(id=1,
                timestamp=datetime.now().timestamp(),
                volume=5.0,
                price=4.5,
                side=Side.SELL,
                type=DataType.ORDER,
                instrument=self._instruments[symbol],
                exchange=self._exchange_type)
            orderbook.add(data)

            data = Data(id=1,
                timestamp=datetime.now().timestamp(),
                volume=4.0,
                price=5.5,
                side=Side.BUY,
                type=DataType.ORDER,
                instrument=self._instruments[symbol],
                exchange=self._exchange_type)
            orderbook.add(data)
            # #############
            # result should be
            #         6.5		2.0
            #         6.0		2.0
            # -----------------------------------------------------
            # 1.0		5.5
            # 2.0		4.0

    def _testOrders(self, count=5):
        for _ in range(count):
            for symbol, orderbook in self._orderbooks.items():
                side = choice((Side.BUY, Side.SELL))
                volume = choice((1.0, 2.0, 3.0))
                price = randint(1, 20)/2.0

                data = Data(id=1,
                            timestamp=datetime.now().timestamp(),
                            volume=volume,
                            price=price,
                            side=side,
                            type=DataType.ORDER,
                            instrument=self._instruments[symbol],
                            exchange=self._exchange_type)
                print(f'adding:\t{data}')
                orderbook.add(data)

    def __repr__(self):
        ret = ''
        for k, v in self._orderbooks.items():
            ret += '--------------------\t' + str(k) + '\t--------------------\n' + str(v)
        return ret

    async def connect(self):
        return

    async def tick(self):
        yield 'test'
        yield 'test2'


Exchange.registerExchange('synthetic', SyntheticExchange)
