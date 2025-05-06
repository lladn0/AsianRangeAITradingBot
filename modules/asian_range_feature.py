# Feature extraction class for backtesting Asian range sweeps
from datetime import datetime, timedelta
from typing import Iterable, List, Dict, Set
import pandas as pd
import os

class AsianRange:

    def __init__(self, ticker: str, candles: Iterable, lookahead: int = 30):
        self.ticker: str = ticker
        self.candles: List = list(candles)
        self.lookahead: int = lookahead

        self._traded_dates: Set[datetime.date] = set()
        self._data: Dict[str, List] = {
            "index": [], "date": [], "asian_high": [], "asian_low": [], "session": [],
            "trade_direction": [], "entry_price": [], "tp1_hit": [], "tp2_hit": [],
            "sl_hit": [], "be_hit": [], "rr_tp1": [], "rr_tp2": [],
            "atr14": [], "ema20": [], "rsi14": [], "macd": [],
            "prev_result": [], "prev_direction": [], "prev_traded": [],
            "day_type": [], "asia_vol": [], "london_vol": []
        }

        self._df: pd.DataFrame | None = None
        self.atr = self.calculate_atr()
        self.ema20 = self.calculate_ema(20)
        self.rsi14 = self.calculate_rsi()
        self.macd = self.calculate_macd()
        self.prev_trade_info: Dict[datetime.date, Dict[str, str]] = {}

    def get_features(self):
        # run the main backtest logic
        self._run_backtest()
        self._df = pd.DataFrame(self._data)
        self.save_to_csv()
        return self._df

    def save_to_csv(self):
        if self._df is None:
            raise ValueError("DataFrame is empty. Call get_features() first.")
        os.makedirs("modules/data/features/", exist_ok=True)
        path = f"modules/data/features/asian_range_{self.ticker}.csv"
        self._df.to_csv(path, index=False)
        print(f"Data saved to {path}")

    def calculate_atr(self, period: int = 14) -> List[float]:
        # manually calculate ATR indicator
        atr = [None] * len(self.candles)
        tr_list = []
        for i in range(1, len(self.candles)):
            high = self.candles[i].high
            low = self.candles[i].low
            prev_close = self.candles[i-1].close
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
            if i >= period:
                atr[i] = round(sum(tr_list[-period:]) / period, 5)
        return atr

    def calculate_ema(self, period: int = 20) -> List[float]:
        # manually calculate EMA
        ema = [None] * len(self.candles)
        k = 2 / (period + 1)
        for i in range(period, len(self.candles)):
            if i == period:
                ema[i] = sum(c.close for c in self.candles[i-period:i]) / period
            else:
                ema[i] = self.candles[i].close * k + ema[i-1] * (1 - k)
        return [round(val, 5) if val else None for val in ema]

    def calculate_rsi(self, period: int = 14) -> List[float]:
        # manually calculate RSI
        rsi = [None] * len(self.candles)
        gains, losses = [], []
        for i in range(1, len(self.candles)):
            delta = self.candles[i].close - self.candles[i - 1].close
            gains.append(max(0, delta))
            losses.append(max(0, -delta))
            if i >= period:
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi[i] = round(100 - (100 / (1 + rs)), 2)
        return rsi

    def calculate_macd(self) -> List[float]:
        ema12 = self.calculate_ema(12)
        ema26 = self.calculate_ema(26)
        return [round(e12 - e26, 5) if e12 and e26 else None for e12, e26 in zip(ema12, ema26)]

    def _run_backtest(self):
        # this is where we simulate the strategy and collect results
        asia_range = {}
        n = len(self.candles)

        for i in range(n):
            candle = self.candles[i]
            c_date = candle.date.date()
            day_type = candle.date.strftime("%A")

            if candle.session == "Asia" and (i == 0 or self.candles[i - 1].session != "Asia"):
                asia_candles = []
                j = i
                while j < n and self.candles[j].session == "Asia":
                    asia_candles.append(self.candles[j])
                    j += 1
                asia_high = max(c.high for c in asia_candles)
                asia_low = min(c.low for c in asia_candles)
                asia_range = {"high": asia_high, "low": asia_low, "vol": asia_high - asia_low}

            if asia_range and candle.session == "London" and c_date not in self._traded_dates:
                trade_dir = None
                entry_price = None
                sl = None

                # detect sweep
                if candle.high > asia_range["high"] > candle.close:
                    trade_dir = "Short"
                    entry_price = candle.close
                    sl = candle.high
                elif candle.low < asia_range["low"] < candle.close:
                    trade_dir = "Long"
                    entry_price = candle.close
                    sl = candle.low

                if trade_dir is None:
                    continue

                tp1 = (asia_range["high"] + asia_range["low"]) / 2
                tp2 = asia_range["low"] if trade_dir == "Short" else asia_range["high"]

                rr_tp1 = rr_tp2 = 0
                if entry_price != sl:
                    if trade_dir == "Long":
                        rr_tp1 = round((tp1 - entry_price) / (entry_price - sl), 2)
                        rr_tp2 = round((tp2 - entry_price) / (entry_price - sl), 2)
                    else:
                        rr_tp1 = round((entry_price - tp1) / (sl - entry_price), 2)
                        rr_tp2 = round((entry_price - tp2) / (sl - entry_price), 2)

                tp1_hit = tp2_hit = sl_hit = be_hit = 0
                active_sl = sl
                london_high, london_low = candle.high, candle.low

                # simulate future candles after entry
                for j in range(i + 1, min(i + 1 + self.lookahead, n)):
                    f = self.candles[j]
                    london_high = max(london_high, f.high)
                    london_low = min(london_low, f.low)
                    if trade_dir == "Short":
                        if f.high >= active_sl:
                            be_hit = 1 if tp1_hit else 0
                            sl_hit = 0 if tp1_hit else 1
                            break
                        if not tp1_hit and f.low <= tp1:
                            tp1_hit = 1
                            active_sl = entry_price
                        if f.low <= tp2:
                            tp2_hit = 1
                            break
                    else:
                        if f.low <= active_sl:
                            be_hit = 1 if tp1_hit else 0
                            sl_hit = 0 if tp1_hit else 1
                            break
                        if not tp1_hit and f.high >= tp1:
                            tp1_hit = 1
                            active_sl = entry_price
                        if f.high >= tp2:
                            tp2_hit = 1
                            break

                prev_date = c_date - timedelta(days=1)
                prev = self.prev_trade_info.get(prev_date, {})

                if any((tp1_hit, tp2_hit, sl_hit, be_hit, entry_price)):
                    self._append_trade(
                        candle.index, candle.date, asia_range["high"], asia_range["low"],
                        candle.session, trade_dir, tp1_hit, tp2_hit, sl_hit, be_hit,
                        entry_price, rr_tp1, rr_tp2, self.atr[i], self.ema20[i], self.rsi14[i],
                        self.macd[i], prev.get("result", "None"), prev.get("direction", "None"),
                        int(bool(prev)), day_type, asia_range["vol"], london_high - london_low
                    )
                    self._traded_dates.add(c_date)
                    self.prev_trade_info[c_date] = {
                        "result": "TP1" if tp1_hit else "TP2" if tp2_hit else "SL" if sl_hit else "BE",
                        "direction": trade_dir
                    }

    def _append_trade(self, idx, date, asia_high, asia_low, session, direction, tp1, tp2, sl,
                      be, entry_price, rr_tp1, rr_tp2, atr, ema20, rsi14, macd,
                      prev_result, prev_direction, prev_traded, day_type,
                      asia_vol, london_vol):
        # store a single row of features into the internal dict
        self._data["index"].append(idx)
        self._data["date"].append(date)
        self._data["asian_high"].append(asia_high)
        self._data["asian_low"].append(asia_low)
        self._data["session"].append(session)
        self._data["trade_direction"].append(direction)
        self._data["tp1_hit"].append(tp1)
        self._data["tp2_hit"].append(tp2)
        self._data["sl_hit"].append(sl)
        self._data["be_hit"].append(be)
        self._data["entry_price"].append(entry_price)
        self._data["rr_tp1"].append(rr_tp1)
        self._data["rr_tp2"].append(rr_tp2)
        self._data["atr14"].append(atr)
        self._data["ema20"].append(ema20)
        self._data["rsi14"].append(rsi14)
        self._data["macd"].append(macd)
        self._data["prev_result"].append(prev_result)
        self._data["prev_direction"].append(prev_direction)
        self._data["prev_traded"].append(prev_traded)
        self._data["day_type"].append(day_type)
        self._data["asia_vol"].append(asia_vol)
        self._data["london_vol"].append(london_vol)