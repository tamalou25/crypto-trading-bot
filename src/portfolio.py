import logging
from datetime import datetime
from colorama import Fore, Style
from tabulate import tabulate

logger = logging.getLogger(__name__)

class Portfolio:
    def __init__(self, capital=1000.0):
        self.initial_capital = capital
        self.cash = capital
        self.positions = {}
        self.trade_history = []
        self.total_pnl = 0
        self.activity_log = []
        self.cycles = 0
    
    def log(self, msg):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        self.activity_log.append(entry)
        if len(self.activity_log) > 50:
            self.activity_log.pop(0)

    def has_position(self, symbol):
        return symbol in self.positions
    
    def get_position(self, symbol):
        return self.positions.get(symbol)
    
    def open_position(self, symbol, price, amount, signal, trade_type='long'):
        cost = price * amount
        self.cash -= cost
        self.positions[symbol] = {
            'symbol': symbol,
            'entry_price': price,
            'amount': amount,
            'cost': cost,
            'entry_time': datetime.now(),
            'highest_price': price,
            'lowest_price': price,
            'signal': signal,
            'trade_type': trade_type
        }
        self.log(f"ACHAT {trade_type.upper()} {symbol} | {amount:.6f} @ {price:.2f} USDT")
        logger.info(f"Position ouverte: {symbol} | {amount:.6f} @ {price:.4f} | Cout: {cost:.2f} USDT")
    
    def close_position(self, symbol, exit_price):
        if symbol not in self.positions:
            return 0
        pos = self.positions.pop(symbol)
        trade_type = pos.get('trade_type', 'long')
        
        if trade_type == 'short':
            pnl = (pos['entry_price'] - exit_price) * pos['amount']
        else:
            pnl = (exit_price - pos['entry_price']) * pos['amount']
        
        revenue = exit_price * pos['amount']
        self.cash += revenue
        self.total_pnl += pnl
        
        trade = {
            'symbol': symbol,
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'amount': pos['amount'],
            'pnl': pnl,
            'pnl_pct': pnl / pos['cost'] * 100,
            'entry_time': pos['entry_time'],
            'exit_time': datetime.now(),
            'trade_type': trade_type
        }
        self.trade_history.append(trade)
        emoji = 'GAIN' if pnl > 0 else 'PERTE'
        self.log(f"{emoji} VENTE {trade_type.upper()} {symbol} | {exit_price:.2f} USDT | PnL: {pnl:+.2f} USDT")
        logger.info(f"Trade ferme: {symbol} | PnL: {pnl:+.2f} USDT ({trade['pnl_pct']:+.2f}%)")
        return pnl
    
    def update_highest_price(self, symbol, price):
        if symbol in self.positions:
            self.positions[symbol]['highest_price'] = price

    def update_lowest_price(self, symbol, price):
        if symbol in self.positions:
            self.positions[symbol]['lowest_price'] = price
    
    def get_total_value(self):
        return self.cash + sum(
            pos['amount'] * pos['entry_price']
            for pos in self.positions.values()
        )
    
    def get_win_rate(self):
        if not self.trade_history:
            return 0
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        return wins / len(self.trade_history) * 100
    
    def print_status(self):
        total_val = self.get_total_value()
        roi = (total_val - self.initial_capital) / self.initial_capital * 100
        print(Fore.CYAN + f"\nPORTFOLIO | Cash: {self.cash:.2f} USDT | Total: {total_val:.2f} USDT | ROI: {roi:+.2f}% | Trades: {len(self.trade_history)}" + Style.RESET_ALL)
