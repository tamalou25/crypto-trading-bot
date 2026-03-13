#!/usr/bin/env python3
"""
AI Crypto Trading Bot - TURBO TEST MODE
Auteur: tamalou25
"""

import os
import sys
import time
import logging
import threading
from dotenv import load_dotenv
from colorama import Fore, Style, init
from apscheduler.schedulers.background import BackgroundScheduler

from src.exchange import ExchangeClient
from src.strategy import TradingStrategy
from src.risk_manager import RiskManager
from src.ml_model import MLSignalModel
from src.portfolio import Portfolio
from src.notifier import TelegramNotifier
from src.dashboard import run_dashboard

init(autoreset=True)
load_dotenv()

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

CYCLE_SECONDS = 30

# Prix en temps reel partagé entre threads
live_prices = {}

def print_banner():
    print(Fore.RED + """
 +===========================================+
 |   AI CRYPTO TRADING BOT - TURBO MODE     |
 |   PAPER TRADING - ARGENT FICTIF          |
 +===========================================+
    """ + Style.RESET_ALL)

def live_price_updater(exchange, pairs):
    """Met a jour les prix toutes les secondes"""
    while True:
        try:
            for pair in pairs:
                ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=2)
                if ohlcv is not None:
                    live_prices[pair] = ohlcv['close'].iloc[-1]
        except:
            pass
        time.sleep(1)

def live_display(portfolio, initial_capital):
    """Affiche le PnL en temps reel toutes les secondes"""
    while True:
        try:
            if live_prices and portfolio.positions:
                # Calcul valeur totale avec prix live
                positions_value = sum(
                    pos['amount'] * live_prices.get(sym, pos['entry_price'])
                    for sym, pos in portfolio.positions.items()
                )
                total = portfolio.cash + positions_value
                pnl = total - initial_capital
                roi = pnl / initial_capital * 100
                
                # Affichage ligne par ligne en temps reel
                color = Fore.GREEN if pnl >= 0 else Fore.RED
                arrow = "▲" if pnl >= 0 else "▼"
                
                # Effacer la ligne et réécrire
                line = f"\r{color}[LIVE] {arrow} Capital: {total:.2f} USDT | PnL: {pnl:+.2f} USDT | ROI: {roi:+.2f}% | Positions: {len(portfolio.positions)}{Style.RESET_ALL}   "
                sys.stdout.write(line)
                sys.stdout.flush()
                
                # Details par paire
                details = []
                for sym, pos in portfolio.positions.items():
                    if sym in live_prices:
                        current = live_prices[sym]
                        pos_pnl = (current - pos['entry_price']) * pos['amount']
                        pos_pct = (current - pos['entry_price']) / pos['entry_price'] * 100
                        c = Fore.GREEN if pos_pnl >= 0 else Fore.RED
                        details.append(f"{c}{sym}: {current:.2f} ({pos_pct:+.2f}%){Style.RESET_ALL}")
                
                if details:
                    sys.stdout.write("\n\r" + " | ".join(details) + "   ")
                    sys.stdout.write(f"\033[1A")  # Remonter d'une ligne
                    sys.stdout.flush()
            
            elif not portfolio.positions:
                sys.stdout.write(f"\r{Fore.YELLOW}[LIVE] En attente de positions... Cash: {portfolio.cash:.2f} USDT{Style.RESET_ALL}   ")
                sys.stdout.flush()
                
        except:
            pass
        time.sleep(1)

def force_buy(exchange, portfolio, risk_manager, pair):
    try:
        ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=10)
        if ohlcv is None:
            return
        current_price = ohlcv['close'].iloc[-1]
        live_prices[pair] = current_price
        if not portfolio.has_position(pair) and risk_manager.can_open_trade(portfolio):
            amount = risk_manager.calculate_position_size(portfolio, current_price)
            order = exchange.place_order(pair, 'buy', amount, current_price)
            if order:
                fake_signal = {'action': 'BUY', 'confidence': 1.0, 'signals': ['FORCE_BUY']}
                portfolio.open_position(pair, current_price, amount, fake_signal)
                print(Fore.GREEN + f"\n>>> [ACHAT] {pair} | {amount:.6f} @ {current_price:.2f} USDT | Investi: {amount*current_price:.2f} USDT" + Style.RESET_ALL)
    except Exception as e:
        print(f"Erreur force_buy {pair}: {e}")

def run_trading_cycle(exchange, strategy, risk_manager, portfolio, pairs):
    for pair in pairs:
        try:
            ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=200)
            if ohlcv is None or len(ohlcv) < 50:
                continue
            
            current_price = ohlcv['close'].iloc[-1]
            live_prices[pair] = current_price
            signal = strategy.generate_signal(ohlcv, pair)
            
            risk_manager.check_open_positions(exchange, portfolio, current_price, pair)
            
            if signal['action'] == 'BUY' and not portfolio.has_position(pair):
                if risk_manager.can_open_trade(portfolio):
                    amount = risk_manager.calculate_position_size(portfolio, current_price)
                    order = exchange.place_order(pair, 'buy', amount, current_price)
                    if order:
                        portfolio.open_position(pair, current_price, amount, signal)
                        print(Fore.GREEN + f"\n>>> [ACHAT] {pair} | {amount:.6f} @ {current_price:.2f} USDT" + Style.RESET_ALL)
            
            elif signal['action'] == 'SELL' and portfolio.has_position(pair):
                pos = portfolio.get_position(pair)
                order = exchange.place_order(pair, 'sell', pos['amount'], current_price)
                if order:
                    pnl = portfolio.close_position(pair, current_price)
                    color = Fore.GREEN if pnl > 0 else Fore.RED
                    print(color + f"\n>>> [VENTE] {pair} | PnL: {pnl:+.2f} USDT" + Style.RESET_ALL)

        except Exception as e:
            logger.error(f"Erreur {pair}: {e}")

def main():
    print_banner()
    
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    capital = 1000.0
    
    print(Fore.YELLOW + f" Capital fictif: {capital} USDT")
    print(Fore.YELLOW + f" Paires: {', '.join(pairs)}")
    print(Fore.RED + f" Cycle trading: {CYCLE_SECONDS}s | Prix live: chaque seconde\n")
    
    exchange = ExchangeClient(mode='paper')
    strategy = TradingStrategy()
    risk_manager = RiskManager()
    ml_model = MLSignalModel()
    portfolio = Portfolio(capital=capital)
    notifier = TelegramNotifier()
    
    ml_model.load_or_train(exchange, 'BTC/USDT')
    strategy.set_ml_model(ml_model)
    
    threading.Thread(target=run_dashboard, args=(portfolio, exchange), daemon=True).start()
    threading.Thread(target=live_price_updater, args=(exchange, pairs), daemon=True).start()
    
    # Force achats immediats
    print(Fore.CYAN + "\n=== FORCE ACHAT INITIAL ===")
    for pair in pairs:
        force_buy(exchange, portfolio, risk_manager, pair)
    
    # Lancer affichage live
    threading.Thread(target=live_display, args=(portfolio, capital), daemon=True).start()
    
    # Scheduler trading toutes les 30s
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_trading_cycle,
        'interval',
        seconds=CYCLE_SECONDS,
        args=[exchange, strategy, risk_manager, portfolio, pairs]
    )
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArret du bot.")
        scheduler.shutdown()

if __name__ == '__main__':
    main()
