#!/usr/bin/env python3
"""
AI Crypto Trading Bot - FULL VERSION
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

os.makedirs('logs', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    handlers=[logging.FileHandler('logs/bot.log', encoding='utf-8')]
)
logger = logging.getLogger(__name__)

PAIRS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
CAPITAL = 1000.0
CYCLE_SECONDS = 30

live_data = {}

def color(val):
    return Fore.GREEN if val >= 0 else Fore.RED

def live_price_updater(exchange):
    while True:
        try:
            for pair in PAIRS:
                ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=3)
                if ohlcv is not None and len(ohlcv) >= 2:
                    c = float(ohlcv['close'].iloc[-1])
                    o = float(ohlcv['open'].iloc[-1])
                    h = float(ohlcv['high'].iloc[-1])
                    l = float(ohlcv['low'].iloc[-1])
                    v = float(ohlcv['volume'].iloc[-1])
                    prev = live_data.get(pair, {}).get('price', c)
                    live_data[pair] = {
                        'price': c, 'open': o, 'high': h, 'low': l,
                        'volume': v,
                        'change_1m': (c - o) / o * 100,
                        'direction': 'up' if c >= prev else 'down'
                    }
        except Exception as e:
            logger.error(f"Price updater error: {e}")
        time.sleep(1)

def render_terminal(portfolio):
    while True:
        try:
            time.sleep(1)
            os.system('cls' if os.name == 'nt' else 'clear')
            now = datetime.now().strftime('%H:%M:%S')

            print(Fore.CYAN + "=" * 72)
            print(f"  AI CRYPTO TRADING BOT  |  {now}  |  PAPER MODE  |  Cycle: {CYCLE_SECONDS}s")
            print("=" * 72 + Style.RESET_ALL)

            # Portfolio
            pos_val = sum(
                live_data.get(s, {}).get('price', p['entry_price']) * p['amount']
                for s, p in portfolio.positions.items()
            )
            total = portfolio.cash + pos_val
            pnl = total - CAPITAL
            roi = pnl / CAPITAL * 100
            arrow = "[+]" if pnl >= 0 else "[-]"
            c = color(pnl)

            print(f"\n  {Fore.YELLOW}PORTFOLIO{Style.RESET_ALL}")
            print(f"  Total: {c}{total:.2f} USDT{Style.RESET_ALL}  |  "
                  f"PnL: {c}{arrow} {pnl:+.2f} USDT ({roi:+.2f}%){Style.RESET_ALL}  |  "
                  f"Cash: {portfolio.cash:.2f}  |  "
                  f"Trades: {len(portfolio.trade_history)}  |  "
                  f"WinRate: {portfolio.get_win_rate():.0f}%")

            # Marche
            print(f"\n  {Fore.YELLOW}MARCHE LIVE{Style.RESET_ALL}")
            print(f"  {'Paire':<14}{'Prix':>10}{'1m%':>9}{'High':>11}{'Low':>11}{'Vol':>12}  Statut")
            print("  " + "-" * 70)
            for pair in PAIRS:
                d = live_data.get(pair)
                if not d:
                    print(f"  {pair:<14} Chargement...")
                    continue
                pc = Fore.GREEN if d['direction'] == 'up' else Fore.RED
                tick = "^" if d['direction'] == 'up' else "v"
                chg_c = Fore.GREEN if d['change_1m'] >= 0 else Fore.RED
                in_pos = pair in portfolio.positions
                if in_pos:
                    pos = portfolio.positions[pair]
                    curr = d['price']
                    ppnl = (curr - pos['entry_price']) / pos['entry_price'] * 100
                    ptype = pos.get('trade_type', 'long').upper()
                    sc = Fore.GREEN if ppnl >= 0 else Fore.RED
                    status = f"{sc}[{ptype}] {ppnl:+.2f}%{Style.RESET_ALL}"
                else:
                    status = f"{Fore.WHITE}[WAIT]{Style.RESET_ALL}"
                print(f"  {pc}{tick} {pair:<12}{Style.RESET_ALL}"
                      f"{pc}{d['price']:>10.2f}{Style.RESET_ALL}"
                      f"{chg_c}{d['change_1m']:>+8.2f}%{Style.RESET_ALL}"
                      f"{d['high']:>11.2f}"
                      f"{d['low']:>11.2f}"
                      f"{d['volume']:>12.1f}  {status}")

            # Positions ouvertes
            if portfolio.positions:
                print(f"\n  {Fore.YELLOW}POSITIONS OUVERTES{Style.RESET_ALL}")
                print(f"  {'Paire':<14}{'Type':<8}{'Entree':>10}{'Actuel':>10}{'PnL $':>10}{'PnL%':>8}{'SL':>10}{'TP':>10}")
                print("  " + "-" * 72)
                for sym, pos in portfolio.positions.items():
                    curr = live_data.get(sym, {}).get('price', pos['entry_price'])
                    ptype = pos.get('trade_type', 'long')
                    if ptype == 'short':
                        ppnl = (pos['entry_price'] - curr) * pos['amount']
                        ppct = (pos['entry_price'] - curr) / pos['entry_price'] * 100
                        sl = pos['entry_price'] * 1.10
                        tp = pos['entry_price'] * 0.80
                    else:
                        ppnl = (curr - pos['entry_price']) * pos['amount']
                        ppct = (curr - pos['entry_price']) / pos['entry_price'] * 100
                        sl = pos['entry_price'] * 0.90
                        tp = pos['entry_price'] * 1.20
                    pc = Fore.GREEN if ppnl >= 0 else Fore.RED
                    tcolor = Fore.GREEN if ptype == 'long' else Fore.RED
                    print(f"  {sym:<14}{tcolor}{ptype.upper():<8}{Style.RESET_ALL}"
                          f"{pos['entry_price']:>10.2f}"
                          f"{pc}{curr:>10.2f}{Style.RESET_ALL}"
                          f"{pc}{ppnl:>+10.2f}{Style.RESET_ALL}"
                          f"{pc}{ppct:>+7.2f}%{Style.RESET_ALL}"
                          f"{Fore.RED}{sl:>10.2f}{Style.RESET_ALL}"
                          f"{Fore.GREEN}{tp:>10.2f}{Style.RESET_ALL}")

            # Derniers trades
            if portfolio.trade_history:
                print(f"\n  {Fore.YELLOW}DERNIERS TRADES{Style.RESET_ALL}")
                print(f"  {'Paire':<14}{'Type':<8}{'Entree':>10}{'Sortie':>10}{'PnL $':>10}{'PnL%':>8}  Heure")
                print("  " + "-" * 68)
                for t in reversed(portfolio.trade_history[-5:]):
                    tc = Fore.GREEN if t['pnl'] > 0 else Fore.RED
                    tcolor = Fore.GREEN if t.get('trade_type','long') == 'long' else Fore.RED
                    exit_t = t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--'
                    print(f"  {t['symbol']:<14}{tcolor}{t.get('trade_type','long').upper():<8}{Style.RESET_ALL}"
                          f"{t['entry_price']:>10.2f}"
                          f"{t['exit_price']:>10.2f}"
                          f"{tc}{t['pnl']:>+10.2f}{Style.RESET_ALL}"
                          f"{tc}{t['pnl_pct']:>+7.2f}%{Style.RESET_ALL}  {exit_t}")

            # Log activite
            if portfolio.activity_log:
                print(f"\n  {Fore.YELLOW}ACTIVITE{Style.RESET_ALL}")
                for msg in portfolio.activity_log[-4:]:
                    print(f"  {Fore.WHITE}{msg}{Style.RESET_ALL}")

            print(f"\n  {Fore.CYAN}Dashboard: http://localhost:5000  |  Ctrl+C pour arreter{Style.RESET_ALL}")
            print(Fore.CYAN + "=" * 72 + Style.RESET_ALL)

        except Exception as e:
            logger.error(f"Render error: {e}")

def do_buy(exchange, portfolio, risk_manager, pair, strategy_signal=None, trade_type='long'):
    """Ouvrir une position LONG ou SHORT"""
    try:
        ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=5)
        if ohlcv is None or len(ohlcv) < 2:
            return
        price = float(ohlcv['close'].iloc[-1])
        live_data[pair] = live_data.get(pair, {'price': price, 'open': price,
            'high': price, 'low': price, 'volume': 0, 'change_1m': 0, 'direction': 'up'})

        if not portfolio.has_position(pair) and risk_manager.can_open_trade(portfolio):
            amount = risk_manager.calculate_position_size(portfolio, price)
            if amount <= 0:
                return
            order = exchange.place_order(pair, 'buy', amount, price)
            if order:
                sig = strategy_signal or {'action': trade_type.upper(), 'confidence': 1.0, 'signals': ['FORCE']}
                sig['trade_type'] = trade_type
                portfolio.open_position(pair, price, amount, sig, trade_type=trade_type)
    except Exception as e:
        logger.error(f"do_buy error {pair}: {e}")

def run_cycle(exchange, strategy, risk_manager, portfolio):
    """Cycle principal: analyse + trade + auto-close en profit"""
    portfolio.cycles = getattr(portfolio, 'cycles', 0) + 1

    for pair in PAIRS:
        try:
            ohlcv = exchange.get_ohlcv(pair, timeframe='1m', limit=200)
            if ohlcv is None or len(ohlcv) < 50:
                continue

            price = float(ohlcv['close'].iloc[-1])
            live_data[pair] = live_data.get(pair, {})
            live_data[pair]['price'] = price

            signal = strategy.generate_signal(ohlcv, pair)
            action = signal['action']
            confidence = signal['confidence']

            # 1. Verifier SL/TP d'abord
            closed = risk_manager.check_open_positions(exchange, portfolio, price, pair)
            if closed:
                # Re-ouvrir immediatement apres fermeture
                time.sleep(0.3)
                new_type = 'long' if action != 'SELL' else 'short'
                do_buy(exchange, portfolio, risk_manager, pair, signal, trade_type=new_type)
                continue

            # 2. Si en position, verifier si profit atteint pour clore et re-trader
            if portfolio.has_position(pair):
                pos = portfolio.positions[pair]
                ptype = pos.get('trade_type', 'long')
                if ptype == 'long':
                    curr_pnl_pct = (price - pos['entry_price']) / pos['entry_price'] * 100
                else:
                    curr_pnl_pct = (pos['entry_price'] - price) / pos['entry_price'] * 100

                # Auto-close si profitable ET signal contraire
                if curr_pnl_pct > 0.5 and (
                    (ptype == 'long' and action == 'SELL') or
                    (ptype == 'short' and action == 'BUY')
                ):
                    order = exchange.place_order(pair, 'sell', pos['amount'], price)
                    if order:
                        pnl = portfolio.close_position(pair, price)
                        time.sleep(0.3)
                        # Re-ouvrir dans le sens du nouveau signal
                        new_type = 'short' if action == 'SELL' else 'long'
                        do_buy(exchange, portfolio, risk_manager, pair, signal, trade_type=new_type)
                continue

            # 3. Ouvrir nouvelle position selon signal
            if action == 'BUY':
                do_buy(exchange, portfolio, risk_manager, pair, signal, trade_type='long')
            elif action == 'SELL':
                do_buy(exchange, portfolio, risk_manager, pair, signal, trade_type='short')

        except Exception as e:
            logger.error(f"Cycle error {pair}: {e}")

def main():
    print(Fore.CYAN + "Demarrage bot..." + Style.RESET_ALL)

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

    # Force achat initial sur toutes les paires
    print(Fore.GREEN + "Force achat initial..." + Style.RESET_ALL)
    for pair in PAIRS:
        do_buy(exchange, portfolio, risk_manager, pair, trade_type='long')
        time.sleep(0.5)

    # Terminal live
    threading.Thread(target=render_terminal, args=(portfolio,), daemon=True).start()

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_cycle, 'interval', seconds=CYCLE_SECONDS,
                      args=[exchange, strategy, risk_manager, portfolio])
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArret.")
        scheduler.shutdown()

if __name__ == '__main__':
    main()
