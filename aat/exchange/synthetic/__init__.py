from ..exchange import Exchange


class SyntheticExchange(Exchange):
    def __init__(self, trading_engine):
        pass

    async def connect(self):
        return

    async def tick(self):
        yield 'test'
        yield 'test2'



Exchange.registerExchange('synthetic', SyntheticExchange)
