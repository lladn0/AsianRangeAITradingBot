import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Handles training and evaluation of the ML model
class Model:
    def __init__(self, ticker: str):
        self.ticker = ticker
        # load pre-made features from file
        self.df = pd.read_csv(f"modules/data/features/asian_range_{ticker}.csv")
        self.label_maps = {}
        self.scaler = None
        self._encode_labels()  # turn categorical labels into numbers
        self.x, self.y = self._select_features()  # input and output columns
        self.model = RandomForestClassifier()  # can change later

    def train(self):
        # split and normalize data, then fit the model
        x_tr, x_te, y_tr, y_te, scaler = self._split_and_scale(self.x, self.y)
        self.scaler = scaler
        self.model.fit(x_tr, y_tr)
        self.save_model()
        print(self.evaluate(x_te, y_te))

    def evaluate(self, x=None, y=None):
        # return precision/recall/f1 report
        if x is None and y is None:
            x, _, y, _ = self._split_and_scale(self.x, self.y)[:4]
        y_pred = self.model.predict(x)
        return classification_report(y, y_pred)

    def save_model(self):
        # save model and metadata to disk
        bundle = {
            "model": self.model,
            "scaler": self.scaler,
            "label_maps": self.label_maps,
            "columns": self.x.columns.tolist(),
        }
        os.makedirs("modules/data/models", exist_ok=True)
        with open(f"modules/data/models/{self.ticker}_model.pkl", "wb") as f:
            pickle.dump(bundle, f)

    def load_model(self):
        # load model and metadata from disk
        with open(f"modules/data/models/{self.ticker}_model.pkl", "rb") as f:
            bundle = pickle.load(f)
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.label_maps = bundle["label_maps"]
        self.feature_order = bundle["columns"]

    def _encode_labels(self):
        # manually encode specific categorical columns
        cat_cols = [
            "session", "trade_direction", "prev_result",
            "prev_direction", "day_type",
        ]
        for col in cat_cols:
            if col in self.df.columns:
                le = LabelEncoder()
                self.df[col] = le.fit_transform(self.df[col])
                self.label_maps[col] = {
                    cls: int(idx) for idx, cls in enumerate(le.classes_)
                }

    def _select_features(self):
        # remove unwanted columns before training
        x = self.df.drop(
            ["tp1_hit", "tp2_hit", "sl_hit", "be_hit", "date", "index"], axis=1
        )
        y = self.df["tp1_hit"]  # predict only TP1 for now
        return x, y

    @staticmethod
    def _split_and_scale(x, y):
        # split into train/test, and normalize
        x_tr, x_te, y_tr, y_te = train_test_split(
            x, y, test_size=0.2, shuffle=False
        )
        scaler = StandardScaler()
        x_tr = scaler.fit_transform(x_tr)
        x_te = scaler.transform(x_te)
        return x_tr, x_te, y_tr, y_te, scaler
