import ccxt
import pandas as pd
import ta
import time
import requests
import os
from datetime import datetime

# =========================
# 🔐 VARIABLES (Railway → Variables)
# =========================
API_KEY = os.getenv("API_KEY")
SECRET = os.getenv("SECRET")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# ⚙️ CONFIG
# =========================
symbol = 'BTC/USDT'
timeframe = '5m'

usdt_por_compra = 12      # mínimo seguro Binance (>10)
take_profit = 0.04        # 4%
stop_loss = 0.05          # 5%
rsi_buy = 40
intervalo = 600           # 10 min

# =========================
# Binance
# =========================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# =========================
# Helpers
# =========================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def telegram(msg):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_data():
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    df = pd.DataFrame(candles, columns=['t','o','h','l','c','v'])

    price = df['c'].iloc[-1]
    rsi = ta.momentum.RSIIndicator(df['c'], 14).rsi().iloc[-1]

    return float(price), float(rsi)

# =========================
# BOT
# =========================
btc = 0
entry = 0

log("🚀 BOT ACTIVO 24/7")

telegram("🤖 Bot iniciado correctamente")

while True:
    try:
        price, rsi = get_data()
        log(f"Precio: {price:.2f} | RSI: {rsi:.2f}")

        # ===== COMPRA =====
        if btc == 0 and rsi < rsi_buy:
            amount = usdt_por_compra / price
            exchange.create_market_buy_order(symbol, amount)

            btc = amount
            entry = price

            msg = f"✅ COMPRA BTC\nPrecio: {price}\nUSDT: {usdt_por_compra}"
            log(msg)
            telegram(msg)

        # ===== TAKE PROFIT =====
        elif btc > 0 and price >= entry * (1 + take_profit):
            exchange.create_market_sell_order(symbol, btc)

            profit = (price - entry) * btc
            msg = f"💰 TAKE PROFIT\nPrecio: {price}\nGanancia: {profit:.2f} USDT"

            btc = 0
            log(msg)
            telegram(msg)

        # ===== STOP LOSS =====
        elif btc > 0 and price <= entry * (1 - stop_loss):
            exchange.create_market_sell_order(symbol, btc)

            loss = (price - entry) * btc
            msg = f"🛑 STOP LOSS\nPrecio: {price}\nResultado: {loss:.2f} USDT"

            btc = 0
            log(msg)
            telegram(msg)

        time.sleep(intervalo)

    except Exception as e:
        log(f"Error: {e}")
        time.sleep(60)
