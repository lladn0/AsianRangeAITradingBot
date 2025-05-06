# Simple class to represent a candlestick
class Candlestick:

    def __init__(self, index, date, open, high, low, close, volume, session):
        self.index = index
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.session = session

    @property
    def is_bull(self):
        return self.close > self.open

    @property
    def is_bear(self):
        return self.close < self.open

    @property
    def body_size(self):
        return abs(self.close - self.open)

    @property
    def shadow_ratio(self):
        # calculates shadow to body ratio
        body = self.body_size
        upper = self.high - max(self.open, self.close)
        lower = min(self.open, self.close) - self.low

        if body == 0:
            return {"overall": 0, "upper": 0, "lower": 0}

        return {
            "overall": (upper + lower) / body,
            "upper": upper / body,
            "lower": lower / body
        }

    @staticmethod
    def asia_range(candles):
        # get Asian session high/low from a list of candles
        if not candles:
            return {"high": None, "low": None}
        return {
            "high": max(candle.high for candle in candles),
            "low": min(candle.low for candle in candles)
        }
