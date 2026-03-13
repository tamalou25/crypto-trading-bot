import pandas as pd
import numpy as np
import logging
from .strategy import TradingStrategy

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, initial_capital=1000, fee=0.001):
        self.initial_capital = initial_capital
        self.fee = fee
        self.strategy = TradingStrategy()

    def run(self, df, symbol='TEST/USDT'):
        capital = self.initial_capital
        position = None
        trades = []
        stop_loss_pct = 0.025
        take_profit_pct = 0.05

        print(f"\n\U0001f50d Backtest {symbol} sur {len(df)} bougies...")

        for i in range(50, len(df) - 1):
            window = df.iloc[:i+1].copy()
            signal = self.strategy.generate_signal(window, symbol)
            price = df['close'].iloc[i]

            if position:
                # Check SL/TP
                sl = position['entry'] * (1 - stop_loss_pct)
                tp = position['entry'] * (1 + take_profit_pct)

                if price <= sl or price >= tp or signal['action'] == 'SELL':
                    pnl = (price - position['entry']) * position['amount'] - price * position['amount'] * self.fee
                    capital += price * position['amount'] * (1 - self.fee)
                    trades.append({
                        'exit_price': price,
                        'entry_price': position['entry'],
                        'pnl': pnl,
                        'reason': 'SL' if price <= sl else ('TP' if price >= tp else 'SIGNAL')
                    })
                    position = None

            elif signal['action'] == 'BUY' and signal['confidence'] >= 0.65 and not position:
                amount = (capital * 0.95) / price
                capital -= price * amount * (1 + self.fee)
                position = {'entry': price, 'amount': amount}

        # Stats
        if not trades:
            print("Aucun trade ex\u00e9cut\u00e9.")
            return

        total_pnl = sum(t['pnl'] for t in trades)
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] <= 0]
        final_capital = self.initial_capital + total_pnl
        roi = (final_capital - self.initial_capital) / self.initial_capital * 100

        print(f"\n\U0001f4ca R\u00c9SULTATS BACKTEST")
        print(f"  Trades: {len(trades)}")
        print(f"  Gagnants: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
        print(f"  Perdants: {len(losses)}")
        print(f"  PnL Total: {total_pnl:+.2f} USDT")
        print(f"  ROI: {roi:+.2f}%")
        print(f"  Capital Final: {final_capital:.2f} USDT")
        if wins:
            print(f"  Meilleur trade: +{max(t['pnl'] for t in wins):.2f} USDT")
        if losses:
            print(f"  Pire trade: {min(t['pnl'] for t in losses):.2f} USDT")

        return trades
