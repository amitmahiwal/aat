import bisect
from collections import deque
from datetime import datetime
from .trade import Trade
from ..config import Side, EventType, DataType
from .data import Data, Event


def _insort(a, x):
    '''insert x into a if not currently there'''
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        # don't insert
        return False
    a.insert(i, x)
    return True


class _PriceLevel(object):
    def __init__(self, price, on_event):
        self._price = price
        self._orders = deque()
        self._on_event = on_event

    def price(self):
        return self._price

    def volume(self):
        return sum((x.volume-x.filled) for x in self._orders)

    def add(self, order):
        self._orders.append(order)

    def cross(self, taker_order):
        while taker_order.filled < taker_order.volume and self._orders:
            # need to fill original volume - filled so far
            to_fill = taker_order.volume - taker_order.filled

            # pop maker order from list
            maker_order = self._orders.popleft()

            # remaining in maker_order
            maker_remaining = maker_order.volume - maker_order.filled

            if maker_remaining > to_fill:
                # maker_order is partially executed
                maker_order.filled += to_fill

                # push back in deque
                self._orders.appendleft(maker_order)

                # will exit loop
                self._on_event(Event(type=EventType.FILL, target=taker_order))
                self._on_event(Event(type=EventType.CHANGE, target=maker_order))
            elif maker_remaining < to_fill:
                # maker_order is fully executed
                # don't append to deque
                # tell maker order filled
                taker_order.filled += maker_remaining
                self._on_event(Event(type=EventType.CHANGE, target=taker_order))
                self._on_event(Event(type=EventType.FILL, target=maker_order))
            else:
                # exactly equal
                maker_order.filled += to_fill
                taker_order.filled += maker_remaining
                self._on_event(Event(type=EventType.FILL, target=taker_order))
                self._on_event(Event(type=EventType.FILL, target=maker_order))

        if taker_order.filled >= taker_order.volume:
            # execute the taker order
            self._on_event(Event(type=EventType.TRADE,
                                 target=Trade(timestamp=datetime.now().timestamp(),
                                              instrument=maker_order.instrument,
                                              price=maker_order.price,
                                              volume=to_fill,
                                              side=taker_order.side,
                                              maker_order=maker_order,
                                              taker_order=taker_order,
                                              exchange=maker_order.exchange)))
            # return nothing to signify to stop
            return None

        # return order, this level is cleared and the order still has volume
        return taker_order

    def __bool__(self):
        return len(self._orders) > 0


class OrderBook(object):
    def __init__(self,
                 instrument,
                 exchange_name='',
                 callback=print):

        self._instrument = instrument
        self._exchange_name = exchange_name

        # levels look like [10, 10.5, 11, 11.5]
        self._buy_levels = []
        self._sell_levels = []

        # look like {price level: PriceLevel}
        self._buys = {}
        self._sells = {}

        # setup callback
        self._callback = callback

    def add(self, order):
        '''add a new order to the order book, potentially triggering events'''
        if order.side == Side.BUY:
            # order is buy, so look at top of sell side
            top = self._sell_levels[0] if len(self._sell_levels) > 0 else float('inf')

            cleared = []

            # check if crosses
            while order.price >= top:
                # execute order against level
                # if returns trade, it cleared the level
                # else, order was fully executed
                trade = self._sells[top].cross(order)

                if trade:
                    # clear sell level
                    cleared.append(top)
                    top = self._sell_levels[len(cleared)] if len(self._sell_levels) > len(cleared) else float('inf')
                    continue

                # trade is done, check if level was cleared exactly
                if not self._sells[top]:
                    # level cleared exactly
                    cleared.append(top)
                break
                

            # clear levels
            self._sell_levels = self._sell_levels[len(cleared):]

            # if order remaining, push to book
            if order.filled < order.volume:
                # push to book
                if _insort(self._buy_levels, order.price):
                    # new price level
                    self._buys[order.price] = _PriceLevel(order.price, self._callback)

                # add order to price level
                self._buys[order.price].add(order)

        else:
            # order is sell, so look at top of buy side
            top = self._buy_levels[-1] if len(self._buy_levels) > 0 else 0

            cleared = []

            # check if crosses
            while order.price <= top:
                # execute order against level
                # if returns trade, it cleared the level
                # else, order was fully executed
                trade = self._buys[top].cross(order)

                if trade:
                    # clear sell level
                    cleared.append(top)
                    top = self._buy_levels[-1-len(cleared)] if len(self._buy_levels) > len(cleared) else 0
                    continue

                # trade is done, check if level was cleared exactly
                if not self._buys[top]:
                    # level cleared exactly
                    cleared.append(top)
                break
                
            # clear levels
            self._buy_levels = self._buy_levels[:-len(cleared)] if len(cleared) else self._buy_levels

            # if order remaining, push to book
            if order.filled < order.volume:
                # push to book
                if _insort(self._sell_levels, order.price):
                    # new price level
                    self._sells[order.price] = _PriceLevel(order.price, self._callback)

                # add order to price level
                self._sells[order.price].add(order)

    def cancel(self, order):
        pass

    def execute(self, maker_order, taker_order):
        pass

    def __repr__(self):
        ret = ''
        # show top 5 levels, then group next 5, 10, 20, etc
        # sells first
        sells = []
        count = 5
        orig = 5
        for i, level in enumerate(self._sell_levels):
            if i < 5:
                # append to list
                sells.append(self._sells[level])
            else:
                if count == orig:
                    sells.append([])
                elif count == 0:
                    # double orig and restart
                    orig = orig * 2
                    count = orig
                # append to last list
                sells[-1].append(self._sells[level])
                count -= 1

        # reverse so visually upside down
        sells.reverse()

        # show top 5 levels, then group next 5, 10, 20, etc
        # sells first
        buys = []
        count = 5
        orig = 5
        for i, level in enumerate(reversed(self._buy_levels)):
            if i < 5:
                # append to list
                buys.append(self._buys[level])
            else:
                if count == orig:
                    buys.append([])
                if count == 0:
                    # double orig and restart
                    orig = orig * 2
                    count = orig
                # append to last list
                buys[-1].append(self._buys[level])
                count -= 1

        # sell list, then line, then buy list
        # if you hit a list, give aggregate
        ret = ''

        for item in sells:
            if isinstance(item, list):
                if len(item) > 1:
                    ret += f'\t\t{item[0].price()} - {item[-1].price()}\t{sum(i.volume() for i in item)}'
                else:
                    ret += f'\t\t{item[0].price()}\t\t{item[0].volume()}'
            else:
                ret += f'\t\t{item.price()}\t\t{item.volume()}'
            ret += '\n'

        ret += '-----------------------------------------------------\n'

        for item in buys:
            if isinstance(item, list):
                if len(item) > 1:
                    ret += f'{sum(i.volume() for i in item)}\t\t{item[0].price()} - {item[-1].price()}\t'
                else:
                    ret += f'{item[0].volume()}\t\t{item[0].price()}'
            else:
                ret += f'{item.volume()}\t\t{item.price()}'
            ret += '\n'

        return ret
