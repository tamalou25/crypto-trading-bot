import pandas as pd
import numpy as np
import ta
import logging

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self):
        self.ml_model = None
    
    def set_ml_model(self, model):
        self.ml_model = model
    
    def compute_indicators(self, df):
        """Calcul de tous les indicateurs techniques"""
        try:
            # Trend
            df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
            df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
            df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
            df['ema_200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_hist'] = macd.macd_diff()
            
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Volume
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # ATR (volatilité)
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            df['atr_pct'] = df['atr'] / df['close'] * 100
            
            # ADX (force de tendance)
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs: {e}")
        
        return df
    
    def technical_signal(self, df):
        """Signal basé sur indicateurs techniques purs"""
        row = df.iloc[-1]
        prev = df.iloc[-2]
        score = 0
        signals = []
        
        # EMA crossover
        if row['ema_9'] > row['ema_21'] and prev['ema_9'] <= prev['ema_21']:
            score += 2
            signals.append('EMA Cross UP')
        elif row['ema_9'] < row['ema_21'] and prev['ema_9'] >= prev['ema_21']:
            score -= 2
            signals.append('EMA Cross DOWN')
        
        # Tendance longue
        if row['close'] > row['ema_200']:
            score += 1
        else:
            score -= 1
        
        # RSI
        if row['rsi'] < 35:
            score += 2
            signals.append('RSI Oversold')
        elif row['rsi'] > 65:
            score -= 2
            signals.append('RSI Overbought')
        elif 45 < row['rsi'] < 60:
            score += 0.5
        
        # MACD
        if row['macd_hist'] > 0 and prev['macd_hist'] <= 0:
            score += 2
            signals.append('MACD Cross UP')
        elif row['macd_hist'] < 0 and prev['macd_hist'] >= 0:
            score -= 2
            signals.append('MACD Cross DOWN')
        elif row['macd_hist'] > prev['macd_hist']:
            score += 0.5
        
        # Bollinger Bands
        if row['bb_pct'] < 0.1:
            score += 1.5
            signals.append('BB Lower Touch')
        elif row['bb_pct'] > 0.9:
            score -= 1.5
            signals.append('BB Upper Touch')
        
        # Volume confirmation
        if row['volume_ratio'] > 1.5:
            score *= 1.2
            signals.append('High Volume')
        
        # ADX
        if row['adx'] > 25:
            if row['adx_pos'] > row['adx_neg']:
                score += 1
            else:
                score -= 1
        
        return score, signals
    
    def generate_signal(self, df, symbol=''):
        """Générer signal final combiné (technique + ML)"""
        df = self.compute_indicators(df.copy())
        df.dropna(inplace=True)
        
        if len(df) < 5:
            return {'action': 'HOLD', 'confidence': 0, 'signals': []}
        
        tech_score, signals = self.technical_signal(df)
        
        # Normaliser score technique (-10 à +10) => confiance 0-1
        tech_confidence = min(abs(tech_score) / 8.0, 1.0)
        tech_action = 'BUY' if tech_score > 2 else ('SELL' if tech_score < -2 else 'HOLD')
        
        # Fusionner avec ML si disponible
        if self.ml_model and self.ml_model.is_trained:
            ml_signal = self.ml_model.predict(df)
            combined_action = tech_action if tech_confidence > 0.7 else ml_signal['action']
            final_confidence = (tech_confidence * 0.6 + ml_signal['confidence'] * 0.4)
        else:
            combined_action = tech_action
            final_confidence = tech_confidence
        
        return {
            'action': combined_action,
            'confidence': final_confidence,
            'tech_score': tech_score,
            'signals': signals,
            'price': df['close'].iloc[-1],
            'atr': df['atr'].iloc[-1]
        }
