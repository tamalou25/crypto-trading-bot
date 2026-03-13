#!/usr/bin/env python3
"""
AI Crypto Trading Bot - Main Entry Point
Auteur: tamalou25
"""

import os
import sys
import time
import logging
from datetime import datetime
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

# Fix Windows Unicode
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

def print_banner():
    print(Fore.CYAN + """
 +===========================================+
 |     AI CRYPTO TRADING BOT                |
 |     github.com/tamalou25                |
 +===========================================+
    """ + Style.RESET_ALL)

def run_trading_cycle(exchange, strategy, risk_manager, portfolio, notifier, pairs):
    """Cycle de trading principal"""
    for pair in pairs:
        try:
            logger.info(f"Analyse de {pair}...")
            
            ohlcv = exchange.get_ohlcv(pair, timeframe=os.getenv('TIMEFRAME', '15m'), limit=200)
            
            if ohlcv is None or len(ohlcv) < 50:
                logger.warning(f"Donnees insuffisantes pour {pair}")
                continue
            
            signal = strategy.generate_signal(ohlcv, pair)
            logger.info(f"Signal {pair}: {signal['action']} (confiance: {signal['confidence']:.2f}) | Score: {signal.get('tech_score', 0):.1f} | {signal.get('signals', [])}")
            
            current_price = ohlcv['close'].iloc[-1]
            
            risk_manager.check_open_positions(exchange, portfolio, current_price, pair)
            
            # Seuil abaisse a 0.40 pour plus d'activite en paper
            if signal['confidence'] >= 0.40:
                if signal['action'] == 'BUY' and not portfolio.has_position(pair):
                    if risk_manager.can_open_trade(portfolio):
                        amount = risk_manager.calculate_position_size(portfolio, current_price)
                        order = exchange.place_order(pair, 'buy', amount, current_price)
                        if order:
                            portfolio.open_position(pair, current_price, amount, signal)
                            notifier.send(f"ACHAT {pair} | Prix: {current_price:.4f} | Montant: {amount:.4f} | Confiance: {signal['confidence']:.0%}")
                            logger.info(f"Position ouverte sur {pair} a {current_price}")
                
                elif signal['action'] == 'SELL' and portfolio.has_position(pair):
                    position = portfolio.get_position(pair)
                    order = exchange.place_order(pair, 'sell', position['amount'], current_price)
                    if order:
                        pnl = portfolio.close_position(pair, current_price)
                        notifier.send(f"VENTE {pair} | Prix: {current_price:.4f} | PnL: {pnl:+.2f} USDT")
                        logger.info(f"Position fermee sur {pair} | PnL: {pnl:+.2f}")
        
        except Exception as e:
            logger.error(f"Erreur sur {pair}: {e}")
            continue

def main():
    print_banner()
    
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    mode = os.getenv('TRADING_MODE', 'paper')
    pairs = os.getenv('TRADING_PAIRS', 'BTC/USDT,ETH/USDT').split(',')
    capital = float(os.getenv('INITIAL_CAPITAL', 1000))
    
    print(Fore.YELLOW + f"\n Mode: {mode.upper()}")
    print(Fore.YELLOW + f" Paires: {', '.join(pairs)}")
    print(Fore.YELLOW + f" Capital: {capital} USDT\n")
    
    if mode == 'live':
        print(Fore.RED + "MODE LIVE ACTIVE - Argent reel utilise!")
        confirm = input("Tape 'OUI' pour confirmer: ")
        if confirm != 'OUI':
            print("Annule.")
            sys.exit(0)
    
    exchange = ExchangeClient(mode=mode)
    strategy = TradingStrategy()
    risk_manager = RiskManager()
    ml_model = MLSignalModel()
    portfolio = Portfolio(capital=capital)
    notifier = TelegramNotifier()
    
    logger.info("Chargement du modele ML...")
    ml_model.load_or_train(exchange, pairs[0])
    strategy.set_ml_model(ml_model)
    
    import threading
    dashboard_thread = threading.Thread(
        target=run_dashboard,
        args=(portfolio, exchange),
        daemon=True
    )
    dashboard_thread.start()
    logger.info("Dashboard disponible sur http://localhost:5000")
    
    scheduler = BackgroundScheduler()
    interval_minutes = 5
    
    scheduler.add_job(
        run_trading_cycle,
        'interval',
        minutes=interval_minutes,
        args=[exchange, strategy, risk_manager, portfolio, notifier, pairs]
    )
    scheduler.start()
    
    logger.info(f"Bot demarre! Cycle toutes les {interval_minutes} minutes")
    
    run_trading_cycle(exchange, strategy, risk_manager, portfolio, notifier, pairs)
    
    try:
        while True:
            portfolio.print_status()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Arret du bot...")
        scheduler.shutdown()

if __name__ == '__main__':
    main()
