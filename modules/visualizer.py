from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Handles plotting of candlesticks with highlights
class Visualizer:

    def __init__(self, ticker):
        self.ticker = ticker
        # load price data and cut down to 100 candles before 10:00
        self.df = pd.read_csv(f"modules/data/price/{ticker}.csv", parse_dates=["Date"])
        cutoff = pd.Timestamp("2025-05-01 10:00", tz="UTC")
        self.df = self.df[self.df["Date"] <= cutoff].tail(100)

    def plot(self):
        # basic candlestick drawing using matplotlib
        df = self.df
        fig, ax = plt.subplots(figsize=(12, 6))

        for _, row in df.iterrows():
            color = 'green' if row["Close"] >= row["Open"] else 'red'
            ax.plot([row["Date"], row["Date"]], [row["Low"], row["High"]], color='black')
            ax.plot([row["Date"], row["Date"]], [row["Open"], row["Close"]], color=color, linewidth=4)

        # highlight Asian session candles
        asia_df = df[df["Session"] == "Asia"]
        for date in asia_df["Date"]:
            ax.axvspan(date, date + pd.Timedelta(minutes=30), color='blue', alpha=0.1)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.set_title(f"{self.ticker}")
        ax.grid(True)
        self.fig = fig  # save fig for export

    def save_plot(self) -> str:
        # save chart to file (for Telegram)
        out_dir = Path("modules/data/photos")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"signal_{datetime.now():%Y%m%d_%H%M%S}.png"
        self.fig.savefig(out_path)
        print("Matplotlib chart saved:", out_path)
        return str(out_path)
