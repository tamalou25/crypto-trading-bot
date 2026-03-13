import ccxt
import os
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExchangeClient:
    def __init__(self, mode='paper'):
        self.mode = mode
        
        # Testnet Binance si TRADING_MODE=paper ou TESTNET=true
        use_testnet = os.getenv('TESTNET', 'true').lower() == 'true' or mode == 'paper'
        
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY', ''),
            'secret': os.getenv('BINANCE_SECRET_KEY', ''),
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        })
        
        # Activer le testnet si besoin
        if use_testnet:
            self.exchange.set_sandbox_mode(True)
        
        self.paper_balance = float(os.getenv('INITIAL_CAPITAL', 1000))
        logger.info(f"Exchange initialise en mode {mode} | Testnet: {use_testnet}")
    
    def get_ohlcv(self, symbol, timeframe='15m', limit=200):
        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Erreur OHLCV {symbol}: {e}")
            return None
    
    def get_ticker(self, symbol):
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Erreur ticker {symbol}: {e}")
            return None
    
    def get_balance(self):
        if self.mode == 'paper':
            return {'USDT': {'free': self.paper_balance}}
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Erreur balance: {e}")
            return None
    
    def place_order(self, symbol, side, amount, price=None):
        if self.mode == 'paper':
            order = {
                'id': f'paper_{datetime.now().timestamp()}',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'status': 'closed',
                'timestamp': datetime.now().timestamp() * 1000
            }
            logger.info(f"[PAPER] {side.upper()} {amount:.6f} {symbol} @ {price}")
            return order
        
        try:
            if side == 'buy':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            logger.info(f"[LIVE] Ordre {side} execute: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Erreur ordre {side} {symbol}: {e}")
            return None
