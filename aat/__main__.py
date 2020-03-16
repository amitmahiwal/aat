import sys
from .trading import TradingEngine


def main(argv: list) -> None:
    # Instantiate trading engine
    #
    # The engine is responsible for managing the different components,
    # including the strategies, the bank/risk engine, and the
    # exchange/backtest engine.
    engine = TradingEngine()

    # Run the live trading engine
    engine.run()


if __name__ == '__main__':
    main(sys.argv)
