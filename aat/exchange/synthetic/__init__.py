import numpy as np
import string
from datetime import datetime
from random import choice, randint, random
from ..exchange import Exchange
from ...core import Instrument, OrderBook, Data, Event
from ...config import Side, DataType, EventType


def _getName(n=1):
    columns = [''.join(np.random.choice(list(string.ascii_uppercase), choice((1, 2, 3, 4)))) + '.' + ''.join(np.random.choice(list(string.ascii_uppercase), choice((1, 2)))) for _ in range(n)]
    return columns


class SyntheticExchange(Exchange):
    def __init__(self, callback=None):
        self._exchange_type = 'synthetic'
        self._callback = callback or print

    def _seed(self, symbols=None):
        self._instruments = {symbol: Instrument(symbol) for symbol in symbols or _getName(1)}
        self._orderbooks = {symbol: OrderBook(instrument=i, exchange_name='synthetic', callback=lambda x:None) for symbol, i in self._instruments.items()}
        self._seedOrders()

    def _seedOrders(self):
        # seed all orderbooks
        for symbol, orderbook in self._orderbooks.items():

            # pick a random startpoint, endpoint, and midpoint
            start = round(random() * 50, 2)
            end = start + round(random() * 50 + 10, 2)
            mid = (start + end)/2.0

            while start < end:
                side = Side.BUY if start <= mid else Side.SELL
                increment = choice((.01, .05, .1, .2))
                orderbook.add(Data(id=1,
                                   timestamp=datetime.now().timestamp(),
                                   volume=round(random()*10, 0),
                                   price=start,
                                   side=side,
                                   type=DataType.ORDER,
                                   instrument=self._instruments[symbol],
                                   exchange=self._exchange_type))
                start = round(start + increment, 2)

    def __repr__(self):
        ret = ''
        for ticker, orderbook in self._orderbooks.items():
            ret += '--------------------\t' + str(ticker) + '\t--------------------\n' + str(orderbook)
        return ret

    async def connect(self):
        '''nothing to connect to'''
        self._seed()

    async def tick(self):
        # first return all seeded orders
        for _, orderbook in self._orderbooks.items():
            for order in orderbook:
                yield Event(type=EventType.OPEN, target=order)

        # choose a random symbol


Exchange.registerExchange('synthetic', SyntheticExchange)
