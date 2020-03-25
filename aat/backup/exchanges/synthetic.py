import ccxt
import pandas as pd
import time
from datetime import datetime
from functools import lru_cache
from numpy.random import normal
from random import randint, random, choice  # noqa: F401
from typing import List
from ..config import SyntheticExchangeConfig
from ..enums import ExchangeType, TickType, Side, PairType, OrderType, CurrencyType, TradingType, ExchangeType_to_string
from ..exchange import Exchange
from ..order_book import OrderBook
from ..structs import MarketData, TradeRequest, TradeResponse, Instrument, Account


class SyntheticExchange(Exchange):
    def __init__(self,
                 exchange_type: ExchangeType,
                 options: SyntheticExchangeConfig,
                 query_engine=None) -> None:
        super(SyntheticExchange, self).__init__(exchange_type=exchange_type, options=options, query_engine=query_engine)
        self._book = OrderBook(options.instruments)
        self._instruments = options.instruments
        self._trading_type = options.trading_type

        # random walk generated by laplace
        # generated order book will skew in this direction
        self._direction = options.direction

        # generated order book will skew with this volatility
        self._volatility = options.volatility

        self._starting_price = 100

        self._underlying_exchange = options.exchange_type
        self._advesaries = []

    def generateMsg(self):
        price = 1000
        while True:
            # take a random walk

            # endpoint
            next_ = normal(self._direction, self._volatility)

            # walk between
            # substeps = normal(self._direction/10, self._volatility/10, randint(1, 10))

            # scale to fill next
            # substeps = substeps*(next_/substeps.cumsum()[-1])
            # for step in substeps:
            #     price += step
            #     price = abs(price)
            price = abs(price + next_)
            data = MarketData(time=datetime.now(),
                              volume=random() * 10,
                              price=price,
                              type=TickType.TRADE,
                              instrument=self._instruments[0],
                              side=choice([Side.BUY, Side.SELL]),
                              exchange=self._underlying_exchange,
                              remaining=random() * 10,
                              sequence=-1,
                              order_type=OrderType.NONE)
            if self._trading_type != TradingType.BACKTEST:
                time.sleep(random() * 3)
            else:
                time.sleep(random() / 500)
            yield data

    async def run(self, trading) -> None:
        while True:
            await self.receive()

    async def receive(self) -> None:
        for msg in self.generateMsg():
            self.callback_data(msg)

    @lru_cache(None)
    def oe_client(self):
        return ccxt.coinbasepro({'enableRateLimit': True})

    async def close(self) -> None:
        '''close the websocket'''
        pass

    @lru_cache(None)
    def accounts(self):
        all_curs = set()
        for inst in self._options.instruments:
            all_curs.add(inst.underlying.value[0])
            all_curs.add(inst.underlying.value[1])

        return {cur: Account(id=str(cur.value),
                             currency=cur,
                             balance=100,
                             exchange=self.exchange(),
                             value=-1,
                             asOf=datetime.now()) for cur in all_curs}

    @lru_cache(None)
    def currencies(self) -> List[CurrencyType]:
        return [CurrencyType(x) for x in self.oe_client().fetch_curencies()]

    @lru_cache(None)
    def markets(self) -> List[Instrument]:
        return [Instrument(underlying=PairType.from_string(m['symbol'])) for m in self.oe_client().fetch_markets()]

    def orderBook(self, level=1):
        '''get order book'''
        raise NotImplementedError()

    def buy(self, req: TradeRequest) -> TradeResponse:
        '''execute a buy order'''
        for ad in self._advesaries:
            req = ad.beforeOrder(req)

        raise NotImplementedError()

        for ad in self._advesaries:
            req = ad.afterOrder(req)

    def sell(self, req: TradeRequest) -> TradeResponse:
        '''execute a sell order'''
        for ad in self._advesaries:
            req = ad.beforeOrder(req)

        raise NotImplementedError()

        for ad in self._advesaries:
            req = ad.afterOrder(req)

    def cancel(self, resp: TradeResponse):
        for ad in self._advesaries:
            resp = ad.beforeOrder(resp)

        raise NotImplementedError()

        for ad in self._advesaries:
            resp = ad.afterOrder(resp)

    def cancelAll(self, resp: TradeResponse):
        pass

    @lru_cache(None)
    def subscription(self):
        return []

    @lru_cache(None)
    def heartbeat(self):
        return []

    def tickToData(self, jsn: dict) -> MarketData:
        pass

    def historical(self, currency_pairs=None, timeframe='1m', since=None, limit=None):
        data = []
        i = 0
        for msg in self.generateMsg():
            # msgs = asyncio.get_event_loop().run_until_complete(asyncio.ensure_future(self.generateMsg()))
            data.append(msg)

            i += 1
            if i > 1000:
                break

        data = [{'timestamp': d.time,
                 'open': d.price,
                 'high': d.price,
                 'low': d.price,
                 'close': d.price,
                 'volume': d.volume} for d in data]

        dfs = [{'pair': str(self._instruments[0].currency_pair),
                'exchange': ExchangeType_to_string(self._underlying_exchange),
                'data': data}]
        df = pd.io.json.json_normalize(dfs, 'data', ['pair', 'exchange'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index(['timestamp', 'pair'], inplace=True)
        df.sort_index(inplace=True)
        return df


class Adversary(object):
    def __init__(self):
        pass

    def beforeData(self, data: MarketData, orig: MarketData) -> MarketData:
        pass

    def afterData(self, market) -> None:
        pass

    def beforeOrder(self, data: TradeRequest, market) -> None:
        pass

    def afterOrder(self, data: TradeResponse, market) -> None:
        pass
