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

CYCLE_SECONDS = 30

def print_banner():
    print(Fore.RED + """
 +===========================================+
 |   AI CRYPTO TRADING BOT - TURBO MODE     |
 |   PAPER TRADING - ARGENT FICTIF          |
 |   Cycle: 30s - Risque max                |
 +===========================================+
    """ + Style.RESET_ALL)

def force_buy(exchange, portfolio, risk_manager, pair):
    """Force un achat immediat sans condition"""
    try:
        ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=10)
        if ohlcv is None:
            return
        current_price = ohlcv['close'].iloc[-1]
        if not portfolio.has_position(pair) and risk_manager.can_open_trade(portfolio):
            amount = risk_manager.calculate_position_size(portfolio, current_price)
            order = exchange.place_order(pair, 'buy', amount, current_price)
            if order:
                fake_signal = {'action': 'BUY', 'confidence': 1.0, 'signals': ['FORCE_BUY']}
                portfolio.open_position(pair, current_price, amount, fake_signal)
                logger.info(Fore.GREEN + f">>> [FORCE] ACHAT {pair} | {amount:.6f} @ {current_price:.2f} USDT | Cout: {amount*current_price:.2f} USDT" + Style.RESET_ALL)
    except Exception as e:
        logger.error(f"Erreur force_buy {pair}: {e}")

def run_trading_cycle(exchange, strategy, risk_manager, portfolio, pairs):
    for pair in pairs:
        try:
            ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=200)
            if ohlcv is None or len(ohlcv) < 50:
                continue
            
            current_price = ohlcv['close'].iloc[-1]
            signal = strategy.generate_signal(ohlcv, pair)
            
            logger.info(f"{pair} | {current_price:.2f} USDT | Signal: {signal['action']} | Score: {signal.get('tech_score',0):.1f}")
            
            # Verifier SL/TP en priorite
            risk_manager.check_open_positions(exchange, portfolio, current_price, pair)
            
            # Ouvrir position si BUY
            if signal['action'] == 'BUY' and not portfolio.has_position(pair):
                if risk_manager.can_open_trade(portfolio):
                    amount = risk_manager.calculate_position_size(portfolio, current_price)
                    order = exchange.place_order(pair, 'buy', amount, current_price)
                    if order:
                        portfolio.open_position(pair, current_price, amount, signal)
                        logger.info(Fore.GREEN + f">>> ACHAT {pair} | {amount:.6f} @ {current_price:.2f} USDT" + Style.RESET_ALL)
            
            # Fermer position si SELL
            elif signal['action'] == 'SELL' and portfolio.has_position(pair):
                pos = portfolio.get_position(pair)
                order = exchange.place_order(pair, 'sell', pos['amount'], current_price)
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
    
    pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    capital = 1000.0
    
    print(Fore.YELLOW + f" Capital fictif: {capital} USDT")
    print(Fore.YELLOW + f" Paires: {', '.join(pairs)}")
    print(Fore.RED + f" Cycle: {CYCLE_SECONDS}s | RISQUE MAX | PAPER ONLY\n")
    
    exchange = ExchangeClient(mode='paper')
    strategy = TradingStrategy()
    risk_manager = RiskManager()
    ml_model = MLSignalModel()
    portfolio = Portfolio(capital=capital)
    notifier = TelegramNotifier()
    
    logger.info("Chargement modele ML...")
    ml_model.load_or_train(exchange, 'BTC/USDT')
    strategy.set_ml_model(ml_model)
    
    import threading
    threading.Thread(target=run_dashboard, args=(portfolio, exchange), daemon=True).start()
    logger.info("Dashboard: http://localhost:5000")
    
    # ============================================
    # FORCE 3 ACHATS IMMEDIATS AU DEMARRAGE
    # ============================================
    logger.info(Fore.CYAN + "=== FORCE ACHAT INITIAL SUR TOUTES LES PAIRES ===")
    for pair in pairs:
        force_buy(exchange, portfolio, risk_manager, pair)
    
    portfolio.print_status()
    
    # Scheduler 30 secondes
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_trading_cycle,
        'interval',
        seconds=CYCLE_SECONDS,
        args=[exchange, strategy, risk_manager, portfolio, pairs]
    )
    scheduler.start()
    logger.info(f"Bot lance! Cycles toutes les {CYCLE_SECONDS} secondes")
    
    try:
        cycle = 0
        while True:
            time.sleep(CYCLE_SECONDS)
            cycle += 1
            portfolio.print_status()
    except KeyboardInterrupt:
        logger.info("Arret du bot.")
        scheduler.shutdown()

if __name__ == '__main__':
    main()
