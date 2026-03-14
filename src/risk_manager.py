import os
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PCT', 0.025))
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PCT', 0.05))
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', 0.15))
        self.max_open_trades = int(os.getenv('MAX_OPEN_TRADES', 3))
        self.trailing_stop = False
    
    def can_open_trade(self, portfolio):
        if portfolio.cash < 10:
            return False
        if len(portfolio.positions) >= self.max_open_trades:
            return False
        return True
    
    def calculate_position_size(self, portfolio, price):
        available = portfolio.cash * self.max_position_size
        amount = available / price
        return round(amount, 6)
    
    def check_open_positions(self, exchange, portfolio, current_price, symbol):
        if not portfolio.has_position(symbol):
            return False
        
        pos = portfolio.get_position(symbol)
        entry_price = pos['entry_price']
        trade_type = pos.get('trade_type', 'long')
        
        if trade_type == 'long':
            pnl_pct = (current_price - entry_price) / entry_price * 100
            sl_trigger = entry_price * (1 - self.stop_loss_pct)
            tp_trigger = entry_price * (1 + self.take_profit_pct)
            should_close = current_price <= sl_trigger or current_price >= tp_trigger
        else:  # short
            pnl_pct = (entry_price - current_price) / entry_price * 100
            sl_trigger = entry_price * (1 + self.stop_loss_pct)
            tp_trigger = entry_price * (1 - self.take_profit_pct)
            should_close = current_price >= sl_trigger or current_price <= tp_trigger
        
        if should_close:
            order = exchange.place_order(symbol, 'sell', pos['amount'], current_price)
            if order:
                pnl = portfolio.close_position(symbol, current_price)
                reason = 'TAKE PROFIT' if pnl > 0 else 'STOP LOSS'
                logger.info(f"{reason} {symbol} @ {current_price:.2f} | PnL: {pnl:+.2f} USDT")
                return True
        return False
