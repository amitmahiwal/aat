from pydantic import BaseModel
from typing import Any
from ..config import Side, DataType, EventType
from .instrument import Instrument


class Event(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    # timestamp: int
    type: EventType
    target: Any

    def __str__(self):
        return f'[{self.type}-{self.target}]'


class Data(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: int
    timestamp: int
    volume: float
    price: float
    side: Side

    type: DataType
    instrument: Instrument

    # maybe specific
    exchange: str
    filled: float = 0.0
    sequence: int = -1

    def __eq__(self, other):
        return (self.price == other.price) and \
               (self.instrument == other.instrument) and \
               (self.side == other.side)

    def __str__(self):
        return f'<{self.instrument}-{self.volume}@{self.price}-{self.type}-{self.exchange}-{self.side}>'

    def __lt__(self, other):
        return self.price < other.price
