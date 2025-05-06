from modules.candle import Candlestick
from modules.asian_range_feature import AsianRange
from modules.model import Model
from modules.collect_data import MT5DataFetcher

import pandas as pd

def main():
    # hardcoded ticker for now
    ticker = "EURUSD"

    # fetch price data and save to csv
    fetcher = MT5DataFetcher(ticker)
    fetcher.get_data()

    # load the csv into DataFrame
    df = pd.read_csv(f"modules/data/price/{ticker}.csv", parse_dates=["Date"])
    print("Data is loaded")

    # convert rows into Candlestick objects
    candles = [Candlestick(row["Index"], row["Date"], row["Open"], row["High"],
                           row["Low"], row["Close"], row["Volume"], row["Session"])
               for _, row in df.iterrows()]
    print(f"Candles created: {len(candles)}")

    # collect features for AI training
    detector = AsianRange(ticker, candles)
    features = detector.get_features()
    print(f"Found patterns: {len(features)}")

    # train model on generated features
    model = Model(ticker)
    model.train()
    model.evaluate()

if __name__ == "__main__":
    main()
