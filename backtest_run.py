#!/usr/bin/env python3
"""
Lancer un backtest sur données historiques
Usage: python backtest_run.py
"""
import os
from dotenv import load_dotenv
from src.exchange import ExchangeClient
from src.backtest import Backtester

load_dotenv()

if __name__ == '__main__':
    print("🔍 Démarrage du backtest...")
    exchange = ExchangeClient(mode='paper')
    
    pairs_to_test = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for pair in pairs_to_test:
        print(f"\n{'='*50}")
        df = exchange.get_ohlcv(pair, timeframe='1h', limit=500)
        if df is not None:
            bt = Backtester(initial_capital=1000)
            bt.run(df, symbol=pair)
        else:
            print(f"Impossible de récupérer les données pour {pair}")
    
    print("\n✅ Backtest terminé!")
