from ..config import EventType
from ..core import Data
from abc import ABCMeta, abstractmethod
from inspect import isabstract


class EventHandler(metaclass=ABCMeta):
    def _valid_callback(self, callback):
        if hasattr(self, callback) and not isabstract(callback):
            return getattr(self, callback)
        return None

    def callback(self, event_type):
        return \
            {EventType.TRADE: self._valid_callback('onTrade'),
            EventType.OPEN: self._valid_callback('onOpen'),
            EventType.CANCEL: self._valid_callback('onCancel'),
            EventType.CHANGE: self._valid_callback('onChange'),
            EventType.FILL: self._valid_callback('onFill'),
            EventType.DATA: self._valid_callback('onData'),
            EventType.HALT: self._valid_callback('onHalt'),
            EventType.CONTINUE: self._valid_callback('onContinue'),
            EventType.ERROR: self._valid_callback('onError'),
            EventType.START: self._valid_callback('onStart'),
            EventType.EXIT: self._valid_callback('onExit')} \
            .get(event_type, None)

    @abstractmethod
    def onTrade(self, data: Data):
        '''onTrade'''

    @abstractmethod
    def onOpen(self, data: Data):
        '''onOpen'''

    @abstractmethod
    def onCancel(self, data: Data):
        '''onCancel'''

    @abstractmethod
    def onChange(self, data: Data):
        '''onChange'''

    @abstractmethod
    def onFill(self, resp: Data):
        '''onFill'''

    @abstractmethod
    def onData(self, data: Data):
        '''onData'''

    @abstractmethod
    def onHalt(self, data):
        '''onHalt'''
        pass

    @abstractmethod
    def onContinue(self, data):
        '''onContinue'''
        pass

    @abstractmethod
    def onError(self, data: Data):
        '''onError'''
        pass

    @abstractmethod
    def onStart(self):
        '''onStart'''
        pass

    @abstractmethod
    def onExit(self):
        '''onExit'''
        pass

    def onAnalyze(self, engine):
        '''onAnalyze'''
        pass

class PrintHandler(EventHandler):
    def onTrade(self, data: Data):
        '''onTrade'''
        print(data)

    def onOpen(self, data: Data):
        '''onOpen'''
        print(data)

    def onCancel(self, data: Data):
        '''onCancel'''
        print(data)

    def onChange(self, data: Data):
        '''onChange'''
        print(data)

    def onFill(self, data: Data):
        '''onFill'''
        print(data)

    def onData(self, data: Data):
        '''onData'''
        print(data)

    def onHalt(self, data: Data):
        '''onHalt'''
        print(data)

    def onContinue(self, data: Data):
        '''onContinue'''
        print(data)

    def onError(self, data: Data):
        '''onError'''
        print(data)

    def onStart(self, data: Data):
        '''onStart'''
        print(data)

    def onExit(self, data: Data):
        '''onExit'''
        print(data)
