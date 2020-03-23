from traitlets.config.application import Application
from traitlets import validate, TraitError, Unicode, Bool


class TradingEngine(Application):
    '''A configureable trading application'''
    name = 'AAT'
    description = 'async algorithmic trading engine'

    verbose = Bool(default_value=True)
    port = Unicode(default_value='8080', help="Port to run on").tag(config=True)
    trading_type = Unicode(default_value='simulation')

    aliases = {
        'port': 'AAT.port',
    }

    @validate('trading_type')
    def _validate_trading_type(self, proposal):
        if proposal['value'] not in ('live', 'simulation', 'backtest'):
            raise TraitError(f'Invalid trading type: {proposal["value"]}')
        return proposal['value']

    def __init__(self, **config):
        self.verbose = bool(config.get('general', {}).get('verbose', False))
        self.trading_typy = bool(config.get('general', {}).get('trading_type', 'simulation'))

    def start(self):
        print('here')