import MetaTrader5 as mt
import pandas as pd
from datetime import datetime, timedelta
from calendar import monthrange
import os

# This class downloads historical candle data from MT5
class MT5DataFetcher:

    def __init__(self, ticker: str, timeframe: int = mt.TIMEFRAME_M30, date_from: datetime = datetime(2020, 1, 1)):
        self.ticker = ticker
        self.timeframe = timeframe
        self.date_from = date_from
        self.df: pd.DataFrame | None = None  # this will hold the result

    def get_data(self) -> pd.DataFrame:
        self._fetch_data()
        self._save_to_csv()
        return self.df

    @staticmethod
    def _last_sunday(year: int, month: int) -> datetime:
        # find last Sunday in given month (used for DST rules)
        d = datetime(year, month, monthrange(year, month)[1])
        while d.weekday() != 6:
            d -= timedelta(days=1)
        return d

    @staticmethod
    def _first_sunday(year: int, month: int) -> datetime:
        # first Sunday of a month
        d = datetime(year, month, 1)
        while d.weekday() != 6:
            d += timedelta(days=1)
        return d

    @staticmethod
    def _determine_session(ts: pd.Timestamp) -> str:
        # figure out what session a candle belongs to (Asia, London, etc)
        year = ts.year
        eu_dst_start = MT5DataFetcher._last_sunday(year, 3)
        eu_dst_end = MT5DataFetcher._last_sunday(year, 10)
        dt_broker = ts.replace(tzinfo=None)

        # Adjust for local time based on DST
        if eu_dst_start <= dt_broker < eu_dst_end:
            local_time = dt_broker
        else:
            local_time = dt_broker - timedelta(hours=1)

        h = local_time.hour
        if 2 <= h < 9:
            return "Asia"
        if 9 <= h < 10:
            return "Frankfurt"
        if 10 <= h < 15:
            return "London"
        if 15 <= h < 23:
            return "New-York"
        return "Other"

    def _connect(self):
        if not mt.initialize():
            raise ConnectionError("MetaTrader5 initialization failed.")

    def _disconnect(self):
        mt.shutdown()

    def _fetch_data(self):
        # download data from MT5 and process it
        date_to: datetime = datetime.now() + timedelta(hours=3)  # MT5 time offset
        self._connect()
        data = mt.copy_rates_range(self.ticker, self.timeframe, self.date_from, date_to)
        self._disconnect()

        if data is None or len(data) == 0:
            raise ValueError("No data returned from MetaTrader5.")

        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit="s").dt.tz_localize("UTC")
        df = df.rename(columns={
            "time": "Date", "open": "Open", "high": "High",
            "low": "Low", "close": "Close", "tick_volume": "Volume",
        })
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df.reset_index(drop=True, inplace=True)
        df["Index"] = df.index
        df["Session"] = df["Date"].apply(self._determine_session)
        self.df = df

    def _save_to_csv(self, path: str | None = None):
        # write DataFrame to CSV file
        if self.df is None:
            raise ValueError("DataFrame is empty.")
        os.makedirs("modules/data/price/", exist_ok=True)
        path = path or f"modules/data/price/{self.ticker}.csv"
        self.df.to_csv(path, index=False)
