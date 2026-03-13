import os
import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import ta

logger = logging.getLogger(__name__)

class MLSignalModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = 'models/trading_model.pkl'
        self.scaler_path = 'models/scaler.pkl'
        self.features = [
            'rsi', 'rsi_fast', 'macd', 'macd_signal', 'macd_hist',
            'bb_pct', 'bb_width', 'stoch_k', 'stoch_d',
            'volume_ratio', 'adx', 'adx_pos', 'adx_neg',
            'atr_pct', 'ema_9', 'ema_21', 'ema_50'
        ]
    
    def prepare_features(self, df):
        """Préparer les features pour le ML"""
        df = df.copy()
        
        # Ajouter indicateurs si pas présents
        if 'rsi' not in df.columns:
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_hist'] = macd.macd_diff()
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_pct'] = (df['close'] - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband())
            df['bb_width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            df['volume_ma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            df['atr_pct'] = df['atr'] / df['close'] * 100
            df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
            df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
            df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        
        # Créer les labels (1=hausse >1.5% dans 12 bougies, 0=sinon)
        df['future_return'] = df['close'].shift(-12) / df['close'] - 1
        df['label'] = (df['future_return'] > 0.015).astype(int)
        
        df.dropna(inplace=True)
        return df
    
    def train(self, df):
        """Entraîner le modèle"""
        df = self.prepare_features(df)
        
        available_features = [f for f in self.features if f in df.columns]
        X = df[available_features].values
        y = df['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = GradientBoostingClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        accuracy = accuracy_score(y_test, self.model.predict(X_test_scaled))
        logger.info(f"🧠 Modèle ML entraîné - Accuracy: {accuracy:.2%}")
        
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        self.is_trained = True
        return accuracy
    
    def load_or_train(self, exchange, symbol):
        """Charger modèle existant ou entraîner"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("✅ Modèle ML chargé depuis disque")
                return
            except:
                pass
        
        logger.info("📊 Entraînement du modèle ML sur données historiques...")
        df = exchange.get_ohlcv(symbol, timeframe='1h', limit=1000)
        if df is not None and len(df) > 100:
            self.train(df)
        else:
            logger.warning("Pas assez de données pour entraîner le ML")
    
    def predict(self, df):
        """Prédire signal sur nouvelles données"""
        if not self.is_trained:
            return {'action': 'HOLD', 'confidence': 0}
        
        try:
            df_prep = self.prepare_features(df.copy())
            available_features = [f for f in self.features if f in df_prep.columns]
            X = df_prep[available_features].iloc[-1:].values
            X_scaled = self.scaler.transform(X)
            
            proba = self.model.predict_proba(X_scaled)[0]
            pred = self.model.predict(X_scaled)[0]
            confidence = proba[pred]
            
            return {
                'action': 'BUY' if pred == 1 else 'SELL',
                'confidence': float(confidence)
            }
        except Exception as e:
            logger.error(f"Erreur prédiction ML: {e}")
            return {'action': 'HOLD', 'confidence': 0}
