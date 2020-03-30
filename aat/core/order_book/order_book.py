from .collector import _Collector
from .price_level import _PriceLevel
from .utils import _insort
from ...config import Side, OrderFlag, OrderType


class OrderBook(object):
    '''A limit order book.

    Supports the following order types:
        - [x] market
            - [x] executes the entire volume
            - [ ] if price specified, will execute (price*volume) worth (e.g. relies on total price, not volume)

            Flags:
                - [x] no flag
                - [ ] fill-or-kill: entire order must fill against current book, otherwise nothing fills
                - [ ] all-or-none: entire order must fill against 1 order, otherwise nothing fills
                - [ ] immediate-or-cancel: same as fill or kill for market orders

        - [x] limit
            - [x] either puts on book or crosses spread, by default puts remainder on book

            Flags:
                - [x] no flag
                - [ ] fill-or-kill: entire order must fill before book moves, otherwise cancelled
                - [ ] all-or-none: entire order must fill against 1 order, otherwise cancelled
                - [ ] immediate-or-cancel: whenever this order executes, fill whatever fills and cancel remaining

        - [ ] stop-market
            - 0 volume order, but when crosses triggers the submission of a market order
        - [ ] stop-limit
            - 0 volume order, but when crosses triggers the submission of a market order

    Supports the following order flags:
        - [x] no flag
        - [ ] fill-or-kill
        - [ ] all-or-none
        - [ ] immediate-or-cancel

    Args:
        instrument (Instrument): the instrument for the book
        exchange_name (str): name of the exchange
        callback (Function): callback on events
    '''

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

        # setup collector for conditional orders
        self._collector = _Collector(callback)

    def setCallback(self, callback):
        self._collector.setCallback(callback)

    def _clearOrders(self, order, amount):
        '''internal'''
        if order.side == Side.BUY:
            self._sell_levels = self._sell_levels[amount:]
        else:
            self._buy_levels = self._buy_levels[:-amount] if amount else self._buy_levels

    def _getTop(self, side, x):
        '''internal'''
        return (self._sell_levels[x] if len(self._sell_levels) > x else None) if side == Side.BUY else (self._buy_levels[-1 - x] if len(self._buy_levels) > x else None)

    def _shouldContinue(self, top, order):
        '''internal'''
        if top is None:
            return False
        return order.price >= top if order.side == Side.BUY else order.price <= top

    def _crossTrade(self, top, order):
        '''internal'''
        if order.side == Side.BUY:
            return self._sells[top].cross(order)
        return self._buys[top].cross(order)

    def _addPriceLevel(self, order):
        '''internal'''
        if order.side == Side.BUY:
            if _insort(self._buy_levels, order.price):
                # new price level
                self._buys[order.price] = _PriceLevel(order.price, collector=self._collector)
            # add order to price level
            self._buys[order.price].add(order)
        else:
            if _insort(self._sell_levels, order.price):
                # new price level
                self._sells[order.price] = _PriceLevel(order.price, collector=self._collector)
            # add order to price level
            self._sells[order.price].add(order)

    def add(self, order):
        '''add a new order to the order book, potentially triggering events:
            EventType.TRADE: if this order crosses the book and fills orders
            EventType.FILL: if this order crosses the book and fills orders
            EventType.CHANGE: if this order crosses the book and partially fills orders
        Args:
            order (Data): order to submit to orderbook
        '''
        # price levels to clear
        cleared = []

        # order is buy, so look at top of sell side
        top = self._getTop(order.side, len(cleared))

        # check if crosses
        while self._shouldContinue(top, order):
            # execute order against level
            # if returns trade, it cleared the level
            # else, order was fully executed
            trade = self._crossTrade(top, order)

            if trade:
                # clear sell level
                cleared.append(top)
                top = self._getTop(order.side, len(cleared))
                continue

            # trade is done, check if level was cleared exactly
            if order.side == Side.BUY:
                if not self._sells[top]:
                    # level cleared exactly
                    cleared.append(top)
            else:
                if not self._buys[top]:
                    # level cleared exactly
                    cleared.append(top)
            break

        # if order remaining, check rules/push to book
        if order.filled < order.volume:
            if order.flag in (OrderFlag.ALL_OR_NONE, OrderFlag.FILL_OR_KILL):
                # cancel the order, do not execute any
                self._collector.clear()

            elif order.flag == OrderFlag.IMMEDIATE_OR_CANCEL:
                # execute the ones that filled, kill the remainder
                self._collector.pushCancel(order)
                self._collector.flush()

                # clear levels
                self._clearOrders(order, len(cleared))

            elif order.order_type == OrderType.LIMIT:
                # execute order
                self._collector.flush()

                # clear levels
                self._clearOrders(order, len(cleared))

                # limit order, put on books
                self._addPriceLevel(order)

            else:
                # market order, partial
                if order.filled > 0:
                    self._collector.pushTrade(order)

                # clear levels
                self._clearOrders(order, len(cleared))

        else:
            # execute all the orders
            self._collector.flush()

            # clear levels
            self._clearOrders(order, len(cleared))

        # clear the collector
        self._collector.clear()

    def cancel(self, order):
        '''remove an order from the order book, potentially triggering events:
            EventType.CANCEL: the cancel event for this
        Args:
            order (Data): order to submit to orderbook
        '''
        price = order.price
        side = order.side

        if side == Side.BUY:
            if price not in self._buy_levels:
                raise Exception('Orderbook out of sync!')
            self._buys[price].remove(order)

            # delete level if no more volume
            if not self._buys[price]:
                self._buy_levels.remove(price)
        else:
            if price not in self._sell_levels:
                raise Exception('Orderbook out of sync!')
            self._sells[price].remove(order)

            # delete level if no more volume
            if not self._sells[price]:
                self._sell_levels.remove(price)

    def topOfBook(self):
        '''return top of both sides

        Args:

        Returns:
            value (dict): returns {'bid': tuple, 'ask': tuple}
        '''
        return {'bid': (self._buy_levels[-1], self._buys[self._buy_levels[-1]].volume()) if len(self._buy_levels) > 0 else (0, 0),
                'ask': (self._sell_levels[0], self._sells[self._sell_levels[0]].volume()) if len(self._sell_levels) > 0 else (float('inf'), 0)}

    def spread(self):
        '''return the spread

        Args:

        Returns:
            value (float): spread between bid and ask
        '''
        tob = self.topOfBook()
        return tob['ask'] - tob['bid']

    def level(self, level=0, price=None, side=None):
        '''return book level

        Args:
            level (int): depth of book to return
            price (float): price level to look for
            side (Side): side to return, or None to return both
        Returns:
            value (tuple): returns ask or bid if Side specified, otherwise ask,bid
        '''
        # collect bids and asks at `level`
        if price:
            bid = (self._buys[price], self._buys[price].volume()) if price in self._buy_levels else None
            ask = (self._sells[price], self._sells[price].volume()) if price in self._sell_levels else None
        else:
            bid = (self._buy_levels[-level], self._buys[self._buy_levels[-level]].volume()) if len(self._buy_levels) > level else None
            ask = (self._sell_levels[level], self._sells[self._sell_levels[level]].volume()) if len(self._sell_levels) > level else None

        if side == Side.SELL:
            return ask
        elif side == Side.BUY:
            return bid
        return ask, bid

    def levels(self, levels=0):
        '''return book levels starting at top

        Args:
            levels (int): number of levels to return
        Returns:
            value (dict of list): returns {"ask": [levels in order], "bid": [levels in order]} for `levels` number of levels
        '''
        if levels <= 0:
            return self.topOfBook()

        ret = self.topOfBook()
        ret['bid'] = [ret['bid']]
        ret['ask'] = [ret['ask']]
        for _ in range(levels):
            ask, bid = self.level(_)
            if ask:
                ret['ask'].append(ask)
            if bid:
                ret['bid'].append(bid)
        return ret

    def __iter__(self):
        '''iterate through asks then bids by level'''
        for level in self._sell_levels:
            for order in self._sells[level]:
                yield order
        for level in self._buy_levels:
            for order in self._buys[level]:
                yield order

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

        # format the sells on top, tabbed to the right, with price\tvolume
        for item in sells:
            if isinstance(item, list):
                # just aggregate these upper levels
                if len(item) > 1:
                    ret += f'\t\t{item[0].price():.2f} - {item[-1].price():.2f}\t{sum(i.volume() for i in item):.2f}'
                else:
                    ret += f'\t\t{item[0].price():.2f}\t\t{item[0].volume():.2f}'
            else:
                ret += f'\t\t{item.price():.2f}\t\t{item.volume():.2f}'
            ret += '\n'

        ret += '-----------------------------------------------------\n'

        # format the buys on bottom, tabbed to the left, with volume\tprice so prices align
        for item in buys:
            if isinstance(item, list):
                # just aggregate these lower levels
                if len(item) > 1:
                    ret += f'{sum(i.volume() for i in item):.2f}\t\t{item[0].price():.2f} - {item[-1].price():.2f}\t'
                else:
                    ret += f'{item[0].volume():.2f}\t\t{item[0].price():.2f}'
            else:
                ret += f'{item.volume():.2f}\t\t{item.price():.2f}'
            ret += '\n'

        return ret
