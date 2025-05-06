# Coursework Project: AI-Based Analysis of Candlestick Patterns for Predicting Price Movements in Financial Markets

### **Student:** Didiura Mikhail

### **Group:** EDIfu24/1

---

## Purpose and Objectives

The goal of this application is to provide real-time trading signals during the London session based on 
machine learning analysis of historical candlestick patterns. The objectives are:

- Automate identification of high-probability reversal trades.
- Apply AI to improve decision-making in trading.
- Deliver fast and visual alerts via Telegram.
- 
## Project Description
This project builds a trading system that tries to forecast if a trade will hit Take Profit 1 (TP1) using historical 
patterns and machine learning. It works with MetaTrader 5, learns from past sweeps of the Asian range, and sends signals 
via Telegram bot during the London trading session.
---


- 
## What It Does
- Loads historical EURUSD data from MT5.
- Finds the Asian session high and low range.
- Simulates price rejections during London session.
- Extracts features: indicators (ATR, EMA, RSI, MACD), Risk to Reward Ratio, session info, etc.
- Trains a machine learning model (`RandomForestClassifier`) to detect good setups.
- In live mode, checks for new trades and sends a prediction to Telegram with a chart.

---

## Project Structure
```plaintext
main_folder/
├── train_model.py               # Full pipeline: fetch → analyze → train → plot
├── live_runner.py        # Starts live monitoring 
├── test_model.py         # Tests if model works and can predict properly

modules/
├── candle.py             # Candlestick object (OHLCV + session)
├── collect_data.py       # MT5 fetcher + time/session labeling logic
├── asian_range_feature.py# Finds Asian sweeps + builds features from them
├── model.py              # Training, saving, evaluating ML model
├── visualizer.py         # Draws candlestick charts and Asian zones
├── bot.py                # Telegram bot to send messages and screenshots
├── base_bot.py           # Abstract base class (OOP: abstraction + inheritance)
├── live_trading.py       # Runs live loop: detect sweeps, predict, alert
```

---

## How Code Works

### 1. **Collecting Data**
- `MT5DataFetcher` connects to MetaTrader 5, downloads historical candles.
- The entire data about candle written in csv (OHLCV) 
- Each candle is labeled based on time: Asia, London, New York, etc.

### 2. **Feature Engineering (Backtest)**
- `AsianRange` class checks if London session sweeps above/below Asian high/low.
- If a sweep happens, we simulate a trade.
- For every trade, we store info like:
  - Was TP1/TP2 hit?
  - Did SL trigger?
  - What was the R:R?
  - What was RSI, MACD, etc.?

### 3. **Model Training**
- `Model` class loads the CSV of features, cleans it up, encodes categories.
- Trains a `RandomForestClassifier` to learn what setups often reach TP1.
- Model + scaler + encoding maps are saved in a `.pkl` file.

### 4. **Live Prediction Loop**
- `LiveTrader` runs during the London session.
- It checks if today’s price swept above or below the Asian range.
- If yes:
  - It builds live features.
  - Predicts if TP1 will hit using the saved model.
  - Sends a chart + message to Telegram.

### 5. **OOP Principles Used**
- **Encapsulation** - All classes use `self._var` to hide inner logic.
- **Abstraction** - `BaseBot` defines what a bot must implement (send message/photo).
- **Inheritance** - `Bot` inherits from `BaseBot`.
- **Polymorphism** - `send_photo()` handles both bytes and file paths.

---

## Technologies Used
- Python 3.10+
- MetaTrader 5 (via `MetaTrader5` library)
- pandas, matplotlib
- scikit-learn
- Telegram Bot API

---

## How to Run

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Add .env file**
```
TELEGRAM_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. **Train the model**
```bash
python train_model.py
```

4. **Start live monitoring**
```bash
python live_runner.py
```

---

## Output Example
On Telegram you’ll get:
- A chart showing price candles
- Asian range highlighted
- Message like “TP prediction” or “SL prediction”

---

## Tests
To make sure the model works:
```bash
python test_model.py -v
```
- Confirms that prediction works with saved model
- Checks if output includes things like `precision`

---

## 🔚 Conclusion and Future Work

This project demonstrates how AI can assist in real-time trading decisions by automating pattern detection and prediction. 
The system integrates technical analysis with machine learning and is deployable in live environments.

### Future Improvements
- Upgrade the algorithm to improve winrate
- Add support for more pairs (e.g. GBPUSD, USDJPY).
- Improve chart visuals
- Develop an alternative trading model (e.g., "Unicorn") with higher win rate and allow the user to choose between models.