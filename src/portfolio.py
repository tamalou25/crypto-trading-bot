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
    
    def has_position(self, symbol):
        return symbol in self.positions
    
    def get_position(self, symbol):
        return self.positions.get(symbol)
    
    def open_position(self, symbol, price, amount, signal):
        cost = price * amount
        self.cash -= cost
        self.positions[symbol] = {
            'symbol': symbol,
            'entry_price': price,
            'amount': amount,
            'cost': cost,
            'entry_time': datetime.now(),
            'highest_price': price,
            'signal': signal
        }
        logger.info(f"Position ouverte: {symbol} | {amount:.6f} @ {price:.4f} | Coût: {cost:.2f} USDT")
    
    def close_position(self, symbol, exit_price):
        if symbol not in self.positions:
            return 0
        pos = self.positions.pop(symbol)
        revenue = exit_price * pos['amount']
        pnl = revenue - pos['cost']
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
            'exit_time': datetime.now()
        }
        self.trade_history.append(trade)
        logger.info(f"Trade fermé: {symbol} | PnL: {pnl:+.2f} USDT ({trade['pnl_pct']:+.2f}%)")
        return pnl
    
    def update_highest_price(self, symbol, price):
        if symbol in self.positions:
            self.positions[symbol]['highest_price'] = price
    
    def get_total_value(self):
        return self.cash + sum(
            pos['amount'] * pos['entry_price'] * 1.0
            for pos in self.positions.values()
        )
    
    def get_win_rate(self):
        if not self.trade_history:
            return 0
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        return wins / len(self.trade_history) * 100
    
    def print_status(self):
        print(Fore.CYAN + "\n📊 === STATUS PORTFOLIO ===")
        total_val = self.get_total_value()
        roi = (total_val - self.initial_capital) / self.initial_capital * 100
        
        print(f" Cash: {self.cash:.2f} USDT")
        print(f" Total: {total_val:.2f} USDT")
        print(f" ROI: {Fore.GREEN if roi >= 0 else Fore.RED}{roi:+.2f}%{Style.RESET_ALL}")
        print(f" PnL Total: {Fore.GREEN if self.total_pnl >= 0 else Fore.RED}{self.total_pnl:+.2f} USDT{Style.RESET_ALL}")
        print(f" Trades: {len(self.trade_history)} | Win Rate: {self.get_win_rate():.1f}%")
        
        if self.positions:
            print(Fore.YELLOW + "\n📈 Positions ouvertes:")
            rows = [[s, f"{p['amount']:.6f}", f"{p['entry_price']:.4f}", f"{p['highest_price']:.4f}"] for s, p in self.positions.items()]
            print(tabulate(rows, headers=['Symbol', 'Amount', 'Entry', 'High'], tablefmt='simple'))
        
        if self.trade_history:
            print(Fore.WHITE + "\n📝 Derniers trades:")
            last_5 = self.trade_history[-5:]
            rows = [[t['symbol'], f"{t['entry_price']:.4f}", f"{t['exit_price']:.4f}", f"{t['pnl']:+.2f}", f"{t['pnl_pct']:+.2f}%"] for t in last_5]
            print(tabulate(rows, headers=['Symbol', 'Entry', 'Exit', 'PnL', '%'], tablefmt='simple'))
        print(Style.RESET_ALL)
