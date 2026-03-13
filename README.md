# 🤖 AI Crypto Trading Bot

> Bot de trading automatique court-terme sur crypto avec signaux ML

## 🚀 Features
- Analyse technique multi-indicateurs (RSI, MACD, Bollinger Bands, EMA)
- Signaux ML avec Random Forest
- Gestion du risque automatique (Stop-Loss / Take-Profit)
- Support Binance (live + paper trading)
- Dashboard Web en temps réel
- Notifications Telegram
- Backtesting intégré

## ⚡ Stack
- Python 3.10+
- CCXT (connexion exchanges)
- Pandas / NumPy / Scikit-learn
- Flask (dashboard web)
- APScheduler (automatisation)
- python-telegram-bot

## 📦 Installation

```bash
git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot
pip install -r requirements.txt
cp .env.example .env
# Édite .env avec tes clés API
python bot.py
```

## 📊 Dashboard
Ouvre http://localhost:5000 après lancement

## ⚠️ Disclaimer
Ce bot est fourni à des fins éducatives. Le trading comporte des risques. Commence TOUJOURS en paper trading.
