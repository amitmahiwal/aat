from perspective import Table
from ..config import EventType
from .data import Data
from .handler import EventHandler


class TableHandler(EventHandler):
    def __init__(self):
        self.onData = None
        self.onHalt = None
        self.onContinue = None
        self.onError = None
        self.onStart = None
        self.onExit = None

        self._trades = Table({})
        self._orders = Table({})

    def tables(self):
        return self._trades, self._orders

    def onTrade(self, data: Data):
        '''onTrade'''
        self._trades.update([data.to_json()])

    def onOpen(self, data: Data):
        '''onOpen'''
        self._orders.update([data.to_json()])

    def onCancel(self, data: Data):
        '''onCancel'''
        self._orders.update([data.to_json()])

    def onChange(self, data: Data):
        '''onChange'''
        self._orders.update([data.to_json()])

    def onFill(self, data: Data):
        '''onFill'''
        self._orders.update([data.to_json()])
