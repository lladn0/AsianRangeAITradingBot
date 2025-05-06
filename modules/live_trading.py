from modules.candle import Candlestick
from modules.collect_data import MT5DataFetcher
from modules.bot import Bot
from datetime import datetime, time as dtime
import pandas as pd
import time
import pickle
import numpy as np
import os
import warnings
from modules.visualizer import Visualizer

# suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Class that handles the live signal detection process
class LiveTrader:
    def __init__(self, ticker):
        self.ticker = ticker
        self.model = None
        self.asian_high = None
        self.asian_low = None
        self.asian_range_ready = False
        self.last_checked_date = None
        self.trade_done_today = False
        self.Bot = Bot()  # init Telegram bot
        self.skip_today = False # if any London's candle closes outside of range - skip day

    def load_model(self):
        # Load trained model from disk
        model_path = f"modules/data/models/EURUSD_model.pkl"
        if not os.path.exists(model_path):
            raise FileNotFoundError("Trained model not found. Train and save first.")

        with open(model_path, "rb") as f:
            bundle = pickle.load(f)

        # Load everything into memory
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.label_maps = bundle["label_maps"]
        self.feature_order = bundle["columns"]
        print("Model + metadata loaded.")

    def fetch_candles(self):
        # Download candles and convert to objects
        fetcher = MT5DataFetcher(self.ticker)
        fetcher.get_data()
        df = pd.read_csv(f"modules/data/price/{self.ticker}.csv", parse_dates=["Date"])
        candles = [Candlestick(row["Index"], row["Date"], row["Open"], row["High"], row["Low"], row["Close"],
                               row["Volume"], row["Session"]) for _, row in df.iterrows()]
        return candles


    def build_asian_range(self, candles, date=None):
        # Take candles for Asian session and define its high/low
        self.skip_today = False
        today = date or candles[-1].date.date()

        asian_candles = [c for c in candles if c.date.date() == today and c.session == "Asia"]
        print(f"Found {len(asian_candles)} Asian candles for {today}")

        if not asian_candles:
            print("No Asian candles found yet.")
            return False

        self.asian_high = max(c.high for c in asian_candles)
        self.asian_low = min(c.low for c in asian_candles)
        self.asian_range_ready = True
        self.trade_done_today = False
        print(f"Asian Range built: High={self.asian_high}, Low={self.asian_low}")
        return True

    def check_sweep_and_predict(self, last_candle):
        # Check if price swept above or below Asian range
        if last_candle.high > self.asian_high:
            trade_dir = "Short"
            print("Sweep above Asian High detected → possible **SELL**.")
        elif last_candle.low < self.asian_low:
            trade_dir = "Long"
            print("Sweep below Asian Low detected → possible **BUY**.")
        else:
            print("No sweep detected.")
            return

        # Build features and run model prediction
        features = self.build_features(last_candle, trade_dir)
        prediction = self.model.predict([features])[0]
        print(f"Prediction (TP-1==1): {prediction}")
        self.trade_done_today = True

        # Based on prediction send chart to Telegram
        if prediction == 1:
            print(f"TP-1 predicted → sending {trade_dir.upper()} screenshot to Telegram …")
            self._send_visual_to_telegram()
            self.Bot.send_message(f"{self.ticker}\n{trade_dir}\nTP prediction")
        elif prediction == 0:
            print(f"SL predicted → sending {trade_dir.upper()} screenshot to Telegram …")
            self._send_visual_to_telegram()
            self.Bot.send_message(f"{self.ticker}\n{trade_dir}\nSL prediction")

    def build_features(self, candle, trade_dir: str) -> list[float]:
        # Basic R:R logic
        tp1 = (self.asian_high + self.asian_low) / 2
        tp2 = self.asian_low if trade_dir == "Short" else self.asian_high
        sl = candle.high if trade_dir == "Short" else candle.low

        rr_tp1 = (tp1 - candle.close) / (candle.close - sl) if trade_dir == "Long" else \
                 (candle.close - tp1) / (sl - candle.close)
        rr_tp2 = (tp2 - candle.close) / (candle.close - sl) if trade_dir == "Long" else \
                 (candle.close - tp2) / (sl - candle.close)

        # Calculate indicators from full candle set
        df = pd.DataFrame([{"High": c.high, "Low": c.low, "Close": c.close} for c in self.fetch_candles()])

        # ATR calc
        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - df["Close"].shift()).abs(),
            (df["Low"] - df["Close"].shift()).abs()
        ], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean().iloc[-1]

        # EMA, RSI, MACD
        ema20 = df["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
        delta = df["Close"].diff()
        up, dn = delta.clip(lower=0), -delta.clip(upper=0)
        gain = up.rolling(14).mean()
        loss = dn.rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi14 = 100 - 100 / (1 + rs.iloc[-1])
        ema12 = df["Close"].ewm(span=12, adjust=False).mean().iloc[-1]
        ema26 = df["Close"].ewm(span=26, adjust=False).mean().iloc[-1]
        macd = ema12 - ema26

        # Additional stats for the day
        asia_vol = self.asian_high - self.asian_low
        london_cs = [c for c in self.fetch_candles()
                     if c.session == "London" and c.date.date() == candle.date.date()]
        london_h = max(c.high for c in london_cs)
        london_l = min(c.low for c in london_cs)
        london_vol = london_h - london_l

        # Bundle into a raw dict of values
        raw = {
            "asian_high": self.asian_high,
            "asian_low": self.asian_low,
            "session": candle.session,
            "trade_direction": trade_dir,
            "entry_price": candle.close,
            "rr_tp1": round(rr_tp1, 2),
            "rr_tp2": round(rr_tp2, 2),
            "atr14": round(atr14, 5),
            "ema20": round(ema20, 5),
            "rsi14": round(rsi14, 2),
            "macd": round(macd, 5),
            "prev_result": "None",
            "prev_direction": "None",
            "prev_traded": 0,
            "day_type": candle.date.strftime("%A"),
            "asia_vol": round(asia_vol, 5),
            "london_vol": round(london_vol, 5),
        }

        # Encode strings into numbers using saved maps
        for col, mapping in self.label_maps.items():
            if col in raw:
                raw[col] = mapping.get(raw[col], -1)

        # Respect original training column order
        vec = [raw[col] for col in self.feature_order]
        vec_scaled = self.scaler.transform([vec])[0]
        return vec_scaled.tolist()

    def check_london_candle_breakout(self, candles):
        today = datetime.now().date()
        london_candles = [c for c in candles if c.session == "London" and c.date.date() == today]

        for candle in london_candles:
            if candle.close > self.asian_high or candle.close < self.asian_low:
                print(f"LONDON candle at {candle.date} closed OUTSIDE Asian Range → skipping day.")
                self.skip_today = True
                return True
        return False

    def _send_visual_to_telegram(self):
        try:
            vis = Visualizer(self.ticker)
            vis.plot()
            path = vis.save_plot()
            self.Bot.send_photo(path)
        except Exception as e:
            print("Error in _send_visual_to_telegram:", e)

    def run(self):
        print("Starting live trading monitor...")
        self.load_model()

        while True:
            now = datetime.now()
            candles = self.fetch_candles()

            if now.time() < dtime(9, 0):
                print("Asian session not finished yet. Waiting...")
                time.sleep(300)
                continue

            today = now.date()
            if not self.asian_range_ready or self.last_checked_date != today:
                built = self.build_asian_range(candles)
                self.last_checked_date = today

                if not built:
                    print("Asian session not finished yet. Waiting...")
                else:
                    print("Asian range built. Waiting for London session to begin...")

                time.sleep(60)
                continue

            last_candle = candles[-1]
            if last_candle.session != "London":
                print("Waiting for London session candle...")
                time.sleep(1800)
                continue

            print(f"Checking candle at {last_candle.date}")

            # Check if London broke the range
            if not self.skip_today:
                self.check_london_candle_breakout(candles)

            if self.skip_today:
                print("Day is marked to be skipped due to London candle closing outside Asian Range.")
                time.sleep(1800)
                continue
            self.check_sweep_and_predict(last_candle)


            time.sleep(180)  # check again in 3 minutes
