# simple script to launch the live trader
from modules.live_trading import LiveTrader

if __name__ == "__main__":
    trader = LiveTrader(ticker="EURUSD")
    trader.run()
