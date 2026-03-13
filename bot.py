#!/usr/bin/env python3
"""
AI Crypto Trading Bot - TURBO TEST MODE
Auteur: tamalou25
"""

import os
import sys
import time
import logging
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
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.01))
CYCLE_SECONDS = int(os.getenv('CYCLE_SECONDS', 30))

def print_banner():
    print(Fore.RED + """
 +===========================================+
 |     AI CRYPTO TRADING BOT - TURBO MODE   |
 |     RISQUE MAX - TEST UNIQUEMENT         |
 |     Cycle: 30 secondes                   |
 +===========================================+
    """ + Style.RESET_ALL)

def run_trading_cycle(exchange, strategy, risk_manager, portfolio, notifier, pairs):
    for pair in pairs:
        try:
            ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=200)
            if ohlcv is None or len(ohlcv) < 50:
                continue
            
            signal = strategy.generate_signal(ohlcv, pair)
            current_price = ohlcv['close'].iloc[-1]
            
            logger.info(f"{pair} | Prix: {current_price:.4f} | {signal['action']} | Confiance: {signal['confidence']:.2f} | Score: {signal.get('tech_score',0):.1f}")
            
            # Verifier SL/TP
            risk_manager.check_open_positions(exchange, portfolio, current_price, pair)
            
            # Executer si signal BUY ou SELL avec confiance > seuil
            if signal['confidence'] >= CONFIDENCE_THRESHOLD:
                if signal['action'] == 'BUY' and not portfolio.has_position(pair):
                    if risk_manager.can_open_trade(portfolio):
                        amount = risk_manager.calculate_position_size(portfolio, current_price)
                        order = exchange.place_order(pair, 'buy', amount, current_price)
                        if order:
                            portfolio.open_position(pair, current_price, amount, signal)
                            logger.info(Fore.GREEN + f">>> ACHAT {pair} | {amount:.6f} @ {current_price:.4f} USDT" + Style.RESET_ALL)
                
                elif signal['action'] == 'SELL' and portfolio.has_position(pair):
                    position = portfolio.get_position(pair)
                    order = exchange.place_order(pair, 'sell', position['amount'], current_price)
                    if order:
                        pnl = portfolio.close_position(pair, current_price)
                        color = Fore.GREEN if pnl > 0 else Fore.RED
                        logger.info(color + f">>> VENTE {pair} | PnL: {pnl:+.2f} USDT" + Style.RESET_ALL)
        
        except Exception as e:
            logger.error(f"Erreur {pair}: {e}")

def main():
    print_banner()
    
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    pairs = os.getenv('TRADING_PAIRS', 'BTC/USDT,ETH/USDT,SOL/USDT').split(',')
    capital = float(os.getenv('INITIAL_CAPITAL', 1000))
    
    print(Fore.YELLOW + f" Capital: {capital} USDT")
    print(Fore.YELLOW + f" Paires: {', '.join(pairs)}")
    print(Fore.RED + f" Cycle: {CYCLE_SECONDS}s | Seuil: {CONFIDENCE_THRESHOLD} | RISQUE MAX\n")
    
    exchange = ExchangeClient(mode='paper')
    strategy = TradingStrategy()
    risk_manager = RiskManager()
    ml_model = MLSignalModel()
    portfolio = Portfolio(capital=capital)
    notifier = TelegramNotifier()
    
    logger.info("Chargement modele ML...")
    ml_model.load_or_train(exchange, pairs[0])
    strategy.set_ml_model(ml_model)
    
    import threading
    threading.Thread(target=run_dashboard, args=(portfolio, exchange), daemon=True).start()
    logger.info("Dashboard: http://localhost:5000")
    
    # Scheduler toutes les 30 secondes
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_trading_cycle,
        'interval',
        seconds=CYCLE_SECONDS,
        args=[exchange, strategy, risk_manager, portfolio, notifier, pairs]
    )
    scheduler.start()
    logger.info(f"TURBO MODE ON - Cycle toutes les {CYCLE_SECONDS} secondes!")
    
    # Premier cycle immediat
    run_trading_cycle(exchange, strategy, risk_manager, portfolio, notifier, pairs)
    
    try:
        cycle = 0
        while True:
            time.sleep(CYCLE_SECONDS)
            cycle += 1
            portfolio.print_status()
            print(Fore.CYAN + f" Cycles effectues: {cycle} | Prochaine analyse dans {CYCLE_SECONDS}s" + Style.RESET_ALL)
    except KeyboardInterrupt:
        logger.info("Arret du bot.")
        scheduler.shutdown()

if __name__ == '__main__':
    main()
