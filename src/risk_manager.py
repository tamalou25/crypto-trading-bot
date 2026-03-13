import os
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PCT', 0.025))
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PCT', 0.05))
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', 0.15))
        self.max_open_trades = int(os.getenv('MAX_OPEN_TRADES', 3))
        self.trailing_stop = os.getenv('TRAILING_STOP', 'true').lower() == 'true'
        logger.info(f"Risk Manager: SL={self.stop_loss_pct*100:.1f}% TP={self.take_profit_pct*100:.1f}%")
    
    def can_open_trade(self, portfolio):
        open_count = len(portfolio.positions)
        if open_count >= self.max_open_trades:
            logger.warning(f"Max trades atteint ({open_count}/{self.max_open_trades})")
            return False
        return True
    
    def calculate_position_size(self, portfolio, price):
        """Kelly-like position sizing basé sur capital disponible"""
        available = portfolio.cash * self.max_position_size
        amount = available / price
        return round(amount, 6)
    
    def check_open_positions(self, exchange, portfolio, current_price, symbol):
        """Vérifier SL/TP sur positions ouvertes"""
        if not portfolio.has_position(symbol):
            return
        
        pos = portfolio.get_position(symbol)
        entry_price = pos['entry_price']
        
        # Trailing stop
        if self.trailing_stop and current_price > pos.get('highest_price', entry_price):
            portfolio.update_highest_price(symbol, current_price)
            high = current_price
        else:
            high = pos.get('highest_price', entry_price)
        
        # Stop Loss (sur prix le plus haut si trailing)
        sl_trigger = high * (1 - self.stop_loss_pct) if self.trailing_stop else entry_price * (1 - self.stop_loss_pct)
        tp_trigger = entry_price * (1 + self.take_profit_pct)
        
        if current_price <= sl_trigger:
            logger.warning(f"🛑 STOP LOSS déclenché sur {symbol} @ {current_price:.4f}")
            order = exchange.place_order(symbol, 'sell', pos['amount'], current_price)
            if order:
                pnl = portfolio.close_position(symbol, current_price)
                logger.info(f"SL fermé: PnL={pnl:+.2f}")
        
        elif current_price >= tp_trigger:
            logger.info(f"✅ TAKE PROFIT déclenché sur {symbol} @ {current_price:.4f}")
            order = exchange.place_order(symbol, 'sell', pos['amount'], current_price)
            if order:
                pnl = portfolio.close_position(symbol, current_price)
                logger.info(f"TP fermé: PnL={pnl:+.2f}")
