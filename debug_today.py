from datetime import datetime
from modules.live_trading import LiveTrader

trader = LiveTrader("EURUSD")
trader.load_model()

candles = trader.fetch_candles()
trader.build_asian_range(candles, datetime(2025, 5, 1).date())  # manually uses May 1 internally

# fixed candle for May 1, 10:00
may_1 = datetime.strptime("2025-05-01 10:00", "%Y-%m-%d %H:%M")
target = [c for c in candles if c.date.strftime("%Y-%m-%d %H:%M") == may_1.strftime("%Y-%m-%d %H:%M")][0]

trader.check_sweep_and_predict(target)
print("done")






