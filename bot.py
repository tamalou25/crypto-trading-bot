#!/usr/bin/env python3
"""
AI Crypto Trading Bot - LIVE TERMINAL DASHBOARD
Auteur: tamalou25
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Back, Style, init
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
    handlers=[logging.FileHandler('logs/bot.log', encoding='utf-8')]
)
logger = logging.getLogger(__name__)

CYCLE_SECONDS = 30
PAIRS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
CAPITAL = 1000.0

# Donnees partagees entre threads
live_data = {}
trade_log = []
stats = {'cycles': 0, 'start_time': datetime.now()}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def color_pct(val):
    if val > 0:
        return Fore.GREEN + f"+{val:.2f}%" + Style.RESET_ALL
    elif val < 0:
        return Fore.RED + f"{val:.2f}%" + Style.RESET_ALL
    return Fore.WHITE + f"{val:.2f}%" + Style.RESET_ALL

def color_val(val, suffix=''):
    if val > 0:
        return Fore.GREEN + f"+{val:.2f}{suffix}" + Style.RESET_ALL
    elif val < 0:
        return Fore.RED + f"{val:.2f}{suffix}" + Style.RESET_ALL
    return Fore.WHITE + f"{val:.2f}{suffix}" + Style.RESET_ALL

def live_price_updater(exchange):
    """Mise a jour prix toutes les secondes"""
    prev_prices = {}
    while True:
        try:
            for pair in PAIRS:
                ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=5)
                if ohlcv is not None and len(ohlcv) >= 2:
                    current = ohlcv['close'].iloc[-1]
                    open_price = ohlcv['open'].iloc[-1]
                    high = ohlcv['high'].iloc[-1]
                    low = ohlcv['low'].iloc[-1]
                    volume = ohlcv['volume'].iloc[-1]
                    change_1m = (current - open_price) / open_price * 100
                    prev = prev_prices.get(pair, current)
                    direction = 'up' if current >= prev else 'down'
                    prev_prices[pair] = current
                    live_data[pair] = {
                        'price': current,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'volume': volume,
                        'change_1m': change_1m,
                        'direction': direction,
                        'updated': datetime.now()
                    }
        except Exception as e:
            logger.error(f"Erreur price updater: {e}")
        time.sleep(1)

def render_dashboard(portfolio):
    """Affiche le dashboard complet toutes les secondes"""
    while True:
        try:
            clear_screen()
            now = datetime.now().strftime('%H:%M:%S')
            uptime = str(datetime.now() - stats['start_time']).split('.')[0]
            
            # HEADER
            print(Fore.CYAN + "=" * 70)
            print(Fore.CYAN + f"   AI CRYPTO TRADING BOT  |  {now}  |  Uptime: {uptime}  |  PAPER MODE")
            print(Fore.CYAN + "=" * 70 + Style.RESET_ALL)
            
            # PORTFOLIO
            positions_value = sum(
                pos['amount'] * live_data.get(sym, {}).get('price', pos['entry_price'])
                for sym, pos in portfolio.positions.items()
            ) if portfolio.positions else 0
            
            total = portfolio.cash + positions_value
            pnl = total - CAPITAL
            roi = pnl / CAPITAL * 100
            
            pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED
            arrow = "[UP]" if pnl >= 0 else "[DOWN]"
            
            print(f"\n  {Fore.YELLOW}PORTFOLIO{Style.RESET_ALL}")
            print(f"  Capital total : {pnl_color}{total:.2f} USDT{Style.RESET_ALL}   "
                  f"PnL: {pnl_color}{arrow} {pnl:+.2f} USDT ({roi:+.2f}%){Style.RESET_ALL}")
            print(f"  Cash dispo    : {Fore.WHITE}{portfolio.cash:.2f} USDT{Style.RESET_ALL}   "
                  f"En position: {Fore.YELLOW}{positions_value:.2f} USDT{Style.RESET_ALL}   "
                  f"Trades fermes: {Fore.WHITE}{len(portfolio.trade_history)}{Style.RESET_ALL}")
            wins = sum(1 for t in portfolio.trade_history if t['pnl'] > 0)
            win_rate = (wins / len(portfolio.trade_history) * 100) if portfolio.trade_history else 0
            print(f"  Win Rate      : {Fore.GREEN if win_rate >= 50 else Fore.RED}{win_rate:.1f}%{Style.RESET_ALL}   "
                  f"Cycles bot: {stats['cycles']}")

            # MARCHE LIVE
            print(f"\n  {Fore.YELLOW}MARCHE EN DIRECT{Style.RESET_ALL}")
            print(f"  {'Paire':<14} {'Prix':>10} {'1m%':>8} {'Haut':>10} {'Bas':>10} {'Volume':>12} {'Signal':>8}")
            print("  " + "-" * 66)
            
            for pair in PAIRS:
                d = live_data.get(pair)
                if d:
                    price_color = Fore.GREEN if d['direction'] == 'up' else Fore.RED
                    tick = "+" if d['direction'] == 'up' else "-"
                    chg_str = color_pct(d['change_1m'])
                    
                    # Signal actuel
                    in_pos = pair in portfolio.positions
                    sig_str = Fore.GREEN + "HOLD" + Style.RESET_ALL
                    if in_pos:
                        pos = portfolio.positions[pair]
                        pos_pnl_pct = (d['price'] - pos['entry_price']) / pos['entry_price'] * 100
                        sig_str = (Fore.GREEN if pos_pnl_pct >= 0 else Fore.RED) + f"IN {pos_pnl_pct:+.2f}%" + Style.RESET_ALL
                    
                    print(f"  {price_color}{tick} {pair:<12}{Style.RESET_ALL} "
                          f"{price_color}{d['price']:>10.2f}{Style.RESET_ALL} "
                          f"{chg_str:>18} "
                          f"{d['high']:>10.2f} "
                          f"{d['low']:>10.2f} "
                          f"{d['volume']:>12.1f} "
                          f"{sig_str}")
                else:
                    print(f"  {pair:<14} {'Chargement...':<50}")
            
            # POSITIONS OUVERTES
            if portfolio.positions:
                print(f"\n  {Fore.YELLOW}POSITIONS OUVERTES ({len(portfolio.positions)}){Style.RESET_ALL}")
                print(f"  {'Paire':<14} {'Entree':>10} {'Actuel':>10} {'Montant':>12} {'PnL $':>10} {'PnL %':>8} {'SL':>10} {'TP':>10}")
                print("  " + "-" * 80)
                for sym, pos in portfolio.positions.items():
                    current = live_data.get(sym, {}).get('price', pos['entry_price'])
                    pos_pnl = (current - pos['entry_price']) * pos['amount']
                    pos_pct = (current - pos['entry_price']) / pos['entry_price'] * 100
                    sl_price = pos['entry_price'] * 0.90
                    tp_price = pos['entry_price'] * 1.20
                    c = Fore.GREEN if pos_pnl >= 0 else Fore.RED
                    print(f"  {sym:<14} "
                          f"{pos['entry_price']:>10.2f} "
                          f"{c}{current:>10.2f}{Style.RESET_ALL} "
                          f"{pos['amount']:>12.6f} "
                          f"{c}{pos_pnl:>+10.2f}{Style.RESET_ALL} "
                          f"{c}{pos_pct:>+7.2f}%{Style.RESET_ALL} "
                          f"{Fore.RED}{sl_price:>10.2f}{Style.RESET_ALL} "
                          f"{Fore.GREEN}{tp_price:>10.2f}{Style.RESET_ALL}")
            
            # DERNIERS TRADES
            if portfolio.trade_history:
                print(f"\n  {Fore.YELLOW}DERNIERS TRADES{Style.RESET_ALL}")
                print(f"  {'Paire':<14} {'Entree':>10} {'Sortie':>10} {'PnL $':>10} {'PnL %':>8} {'Heure'}")
                print("  " + "-" * 66)
                for t in reversed(portfolio.trade_history[-5:]):
                    c = Fore.GREEN if t['pnl'] > 0 else Fore.RED
                    exit_time = t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--'
                    print(f"  {t['symbol']:<14} "
                          f"{t['entry_price']:>10.2f} "
                          f"{t['exit_price']:>10.2f} "
                          f"{c}{t['pnl']:>+10.2f}{Style.RESET_ALL} "
                          f"{c}{t['pnl_pct']:>+7.2f}%{Style.RESET_ALL} "
                          f"{exit_time}")
            
            # LOG ACTIVITE
            if trade_log:
                print(f"\n  {Fore.YELLOW}ACTIVITE RECENTE{Style.RESET_ALL}")
                for msg in trade_log[-4:]:
                    print(f"  {msg}")
            
            print(f"\n  {Fore.CYAN}Dashboard web: http://localhost:5000  |  Ctrl+C pour arreter{Style.RESET_ALL}")
            print(Fore.CYAN + "=" * 70 + Style.RESET_ALL)

        except Exception as e:
            pass
        time.sleep(1)

def force_buy(exchange, portfolio, risk_manager, pair):
    try:
        ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=5)
        if ohlcv is None:
            return
        current_price = ohlcv['close'].iloc[-1]
        live_data[pair] = {'price': current_price, 'open': current_price, 'high': current_price,
                           'low': current_price, 'volume': 0, 'change_1m': 0, 'direction': 'up', 'updated': datetime.now()}
        if not portfolio.has_position(pair) and risk_manager.can_open_trade(portfolio):
            amount = risk_manager.calculate_position_size(portfolio, current_price)
            order = exchange.place_order(pair, 'buy', amount, current_price)
            if order:
                fake_signal = {'action': 'BUY', 'confidence': 1.0, 'signals': ['FORCE_BUY']}
                portfolio.open_position(pair, current_price, amount, fake_signal)
                msg = f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ACHAT {pair} | {amount:.6f} @ {current_price:.2f} USDT | Investi: {amount*current_price:.2f} USDT{Style.RESET_ALL}"
                trade_log.append(msg)
                logger.info(f"ACHAT {pair} @ {current_price}")
    except Exception as e:
        logger.error(f"Erreur force_buy {pair}: {e}")

def run_trading_cycle(exchange, strategy, risk_manager, portfolio):
    stats['cycles'] += 1
    for pair in PAIRS:
        try:
            ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=200)
            if ohlcv is None or len(ohlcv) < 50:
                continue
            current_price = ohlcv['close'].iloc[-1]
            signal = strategy.generate_signal(ohlcv, pair)
            risk_manager.check_open_positions(exchange, portfolio, current_price, pair)
            
            if signal['action'] == 'BUY' and not portfolio.has_position(pair):
                if risk_manager.can_open_trade(portfolio):
                    amount = risk_manager.calculate_position_size(portfolio, current_price)
                    order = exchange.place_order(pair, 'buy', amount, current_price)
                    if order:
                        portfolio.open_position(pair, current_price, amount, signal)
                        msg = f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ACHAT {pair} @ {current_price:.2f} | Confiance: {signal['confidence']:.0%}{Style.RESET_ALL}"
                        trade_log.append(msg)
            
            elif signal['action'] == 'SELL' and portfolio.has_position(pair):
                pos = portfolio.get_position(pair)
                order = exchange.place_order(pair, 'sell', pos['amount'], current_price)
                if order:
                    pnl = portfolio.close_position(pair, current_price)
                    c = Fore.GREEN if pnl > 0 else Fore.RED
                    msg = f"{c}[{datetime.now().strftime('%H:%M:%S')}] VENTE {pair} @ {current_price:.2f} | PnL: {pnl:+.2f} USDT{Style.RESET_ALL}"
                    trade_log.append(msg)
        except Exception as e:
            logger.error(f"Erreur cycle {pair}: {e}")
    
    # Garder seulement les 20 derniers logs
    if len(trade_log) > 20:
        trade_log.pop(0)

def main():
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print(Fore.CYAN + "Demarrage du bot..." + Style.RESET_ALL)
    
    exchange = ExchangeClient(mode='paper')
    strategy = TradingStrategy()
    risk_manager = RiskManager()
    ml_model = MLSignalModel()
    portfolio = Portfolio(capital=CAPITAL)
    notifier = TelegramNotifier()
    
    print("Chargement modele ML...")
    ml_model.load_or_train(exchange, 'BTC/USDT')
    strategy.set_ml_model(ml_model)
    
    # Threads
    threading.Thread(target=run_dashboard, args=(portfolio, exchange), daemon=True).start()
    threading.Thread(target=live_price_updater, args=(exchange,), daemon=True).start()
    
    # Force achats initiaux
    print("Force achat initial sur toutes les paires...")
    for pair in PAIRS:
        force_buy(exchange, portfolio, risk_manager, pair)
    
    # Lancer dashboard terminal
    threading.Thread(target=render_dashboard, args=(portfolio,), daemon=True).start()
    
    # Scheduler trading
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_trading_cycle, 'interval', seconds=CYCLE_SECONDS,
        args=[exchange, strategy, risk_manager, portfolio]
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
