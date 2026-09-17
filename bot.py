import os

import requests

import pandas as pd

TWELVE_API_KEY = os.environ["TWELVE_API_KEY"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

CHAT_ID = "8969188333"

# USD/JPY 1-minute candles

url = "https://api.twelvedata.com/time_series"

params = {

    "symbol": "USD/JPY",

    "interval": "1min",

    "outputsize": 100,

    "apikey": TWELVE_API_KEY

}

data = requests.get(url, params=params, timeout=20).json()

if "values" not in data:

    raise Exception(f"Twelve Data error: {data}")

df = pd.DataFrame(data["values"])

df = df.iloc[::-1].reset_index(drop=True)

for col in ["open", "high", "low", "close"]:

    df[col] = pd.to_numeric(df[col])

# EMA

df["EMA9"] = df["close"].ewm(span=9, adjust=False).mean()

df["EMA21"] = df["close"].ewm(span=21, adjust=False).mean()

# RSI

delta = df["close"].diff()

gain = delta.clip(lower=0)

loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()

avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss

df["RSI"] = 100 - (100 / (1 + rs))

# MACD

ema12 = df["close"].ewm(span=12, adjust=False).mean()

ema26 = df["close"].ewm(span=26, adjust=False).mean()

df["MACD"] = ema12 - ema26

df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

last = df.iloc[-1]

signal = "WAIT"

if (

    last["close"] > last["EMA9"] > last["EMA21"]

    and 50 < last["RSI"] < 70

    and last["MACD"] > last["MACD_signal"]

):

    signal = "CALL"

elif (

    last["close"] < last["EMA9"] < last["EMA21"]

    and 30 < last["RSI"] < 50

    and last["MACD"] < last["MACD_signal"]

):

    signal = "PUT"

message = (

    "📊 USD/JPY Signal\n\n"

    f"Signal: {signal}\n"

    f"Price: {last['close']:.3f}\n"

    f"RSI: {last['RSI']:.2f}\n"

    f"EMA9: {last['EMA9']:.3f}\n"

    f"EMA21: {last['EMA21']:.3f}\n"

    f"MACD: {last['MACD']:.5f}\n\n"

    "⚠️ Educational signal — confirm on your Quotex chart."

)

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

requests.post(

    telegram_url,

    data={

        "chat_id": CHAT_ID,

        "text": message

    },

    timeout=20

).raise_for_status()

