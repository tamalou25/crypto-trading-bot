import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Moteur d'analyse complet:
    - 20+ indicateurs techniques
    - Multi-timeframe (1m, 5m, 15m)
    - Reconnaissance de patterns (chandeliers)
    - Analyse de volume avancee
    - Score de sentiment global
    - Systeme de vote pondere
    """

    def compute_all(self, df):
        """Calcule tous les indicateurs sur un DataFrame OHLCV"""
        try:
            import ta
            c = df['close']
            h = df['high']
            l = df['low']
            v = df['volume']

            # === TREND ===
            for w in [9, 21, 50, 100, 200]:
                df[f'ema{w}'] = c.ewm(span=w, adjust=False).mean()
            for w in [10, 20, 50]:
                df[f'sma{w}'] = c.rolling(w).mean()

            # MACD triple
            for fast, slow, sig in [(12,26,9),(5,13,4),(8,21,5)]:
                ema_f = c.ewm(span=fast).mean()
                ema_s = c.ewm(span=slow).mean()
                macd = ema_f - ema_s
                signal = macd.ewm(span=sig).mean()
                df[f'macd_{fast}_{slow}'] = macd
                df[f'macd_sig_{fast}_{slow}'] = signal
                df[f'macd_hist_{fast}_{slow}'] = macd - signal

            # Ichimoku
            h9  = h.rolling(9).max();  l9  = l.rolling(9).min()
            h26 = h.rolling(26).max(); l26 = l.rolling(26).min()
            h52 = h.rolling(52).max(); l52 = l.rolling(52).min()
            df['tenkan']  = (h9 + l9) / 2
            df['kijun']   = (h26 + l26) / 2
            df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
            df['senkou_b'] = ((h52 + l52) / 2).shift(26)
            df['chikou']  = c.shift(-26)

            # Parabolic SAR
            try:
                df['psar'] = ta.trend.PSARIndicator(h, l, c).psar()
                df['psar_up'] = ta.trend.PSARIndicator(h, l, c).psar_up()
                df['psar_down'] = ta.trend.PSARIndicator(h, l, c).psar_down()
            except: pass

            # === MOMENTUM ===
            df['rsi14'] = ta.momentum.RSIIndicator(c, 14).rsi()
            df['rsi7']  = ta.momentum.RSIIndicator(c, 7).rsi()
            df['rsi21'] = ta.momentum.RSIIndicator(c, 21).rsi()

            stoch = ta.momentum.StochasticOscillator(h, l, c, 14, 3)
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()

            df['roc']  = ta.momentum.ROCIndicator(c, 10).roc()
            df['roc3'] = ta.momentum.ROCIndicator(c, 3).roc()
            df['cci']  = ta.trend.CCIIndicator(h, l, c, 20).cci()
            df['williams_r'] = ta.momentum.WilliamsRIndicator(h, l, c, 14).williams_r()
            df['tsi'] = ta.momentum.TSIIndicator(c).tsi()

            # === VOLATILITE ===
            bb = ta.volatility.BollingerBands(c, 20, 2)
            df['bb_up']  = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_pct'] = bb.bollinger_pband()
            df['bb_w']   = bb.bollinger_wband()

            bb1 = ta.volatility.BollingerBands(c, 20, 1)
            df['bb1_up']  = bb1.bollinger_hband()
            df['bb1_low'] = bb1.bollinger_lband()

            df['atr']   = ta.volatility.AverageTrueRange(h, l, c, 14).average_true_range()
            df['atr_pct'] = df['atr'] / c * 100
            df['kc_up'] = ta.volatility.KeltnerChannel(h, l, c, 20).keltner_channel_hband()
            df['kc_low']= ta.volatility.KeltnerChannel(h, l, c, 20).keltner_channel_lband()

            # Squeeze Momentum (BB dans KC = squeeze)
            df['squeeze'] = (df['bb_up'] < df['kc_up']) & (df['bb_low'] > df['kc_low'])

            # === TREND FORCE ===
            adx = ta.trend.ADXIndicator(h, l, c, 14)
            df['adx']    = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()

            df['aroon_up']   = ta.trend.AroonIndicator(h, l, 25).aroon_up()
            df['aroon_down'] = ta.trend.AroonIndicator(h, l, 25).aroon_down()
            df['aroon_osc']  = df['aroon_up'] - df['aroon_down']

            # === VOLUME ===
            df['vol_ma20']   = v.rolling(20).mean()
            df['vol_ratio']  = v / (df['vol_ma20'] + 0.001)
            df['obv']        = ta.volume.OnBalanceVolumeIndicator(c, v).on_balance_volume()
            df['obv_ema']    = df['obv'].ewm(span=21).mean()
            df['vwap']       = (c * v).cumsum() / v.cumsum()
            df['mfi']        = ta.volume.MFIIndicator(h, l, c, v, 14).money_flow_index()
            try:
                df['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(h, l, c, v, 20).chaikin_money_flow()
            except: pass

            # === SUPPORT / RESISTANCE ===
            df['pivot']  = (h.shift(1) + l.shift(1) + c.shift(1)) / 3
            df['r1']     = 2 * df['pivot'] - l.shift(1)
            df['s1']     = 2 * df['pivot'] - h.shift(1)
            df['r2']     = df['pivot'] + (h.shift(1) - l.shift(1))
            df['s2']     = df['pivot'] - (h.shift(1) - l.shift(1))

            # === CHANDELIERS JAPONAIS ===
            df['body']   = abs(c - df['open'])
            df['range']  = h - l
            df['body_pct'] = df['body'] / (df['range'] + 0.0001)
            df['is_bull']  = c > df['open']

        except Exception as e:
            logger.error(f"compute_all error: {e}")
        return df

    def detect_patterns(self, df):
        """Detection de patterns chandeliers"""
        patterns = []
        if len(df) < 5: return patterns
        c0 = df.iloc[-1]; c1 = df.iloc[-2]; c2 = df.iloc[-3]

        body0 = abs(c0['close'] - c0['open'])
        body1 = abs(c1['close'] - c1['open'])
        range0 = c0['high'] - c0['low']

        # Doji
        if body0 / (range0 + 0.0001) < 0.1:
            patterns.append(('DOJI', 0, 'Indecision'))

        # Marteau (Hammer) = signal haussier
        low_wick = c0['open'] - c0['low'] if c0['open'] < c0['close'] else c0['close'] - c0['low']
        up_wick  = c0['high'] - c0['close'] if c0['open'] < c0['close'] else c0['high'] - c0['open']
        if low_wick > 2 * body0 and up_wick < body0 and c0['close'] > c0['open']:
            patterns.append(('HAMMER', 2, 'Hausse'))

        # Shooting Star = signal baissier
        if up_wick > 2 * body0 and low_wick < body0 and c0['close'] < c0['open']:
            patterns.append(('SHOOTING_STAR', -2, 'Baisse'))

        # Engulfing haussier
        if (c1['close'] < c1['open'] and c0['close'] > c0['open']
                and c0['open'] <= c1['close'] and c0['close'] >= c1['open']):
            patterns.append(('BULL_ENGULFING', 3, 'Forte hausse'))

        # Engulfing baissier
        if (c1['close'] > c1['open'] and c0['close'] < c0['open']
                and c0['open'] >= c1['close'] and c0['close'] <= c1['open']):
            patterns.append(('BEAR_ENGULFING', -3, 'Forte baisse'))

        # Morning Star
        if (c2['close'] < c2['open'] and
                abs(c1['close'] - c1['open']) < abs(c2['close'] - c2['open']) * 0.3 and
                c0['close'] > c0['open'] and c0['close'] > (c2['open'] + c2['close']) / 2):
            patterns.append(('MORNING_STAR', 3, 'Forte hausse'))

        # Evening Star
        if (c2['close'] > c2['open'] and
                abs(c1['close'] - c1['open']) < abs(c2['close'] - c2['open']) * 0.3 and
                c0['close'] < c0['open'] and c0['close'] < (c2['open'] + c2['close']) / 2):
            patterns.append(('EVENING_STAR', -3, 'Forte baisse'))

        # Three White Soldiers
        if all(df.iloc[-i]['close'] > df.iloc[-i]['open'] for i in [1,2,3]):
            if df.iloc[-1]['close'] > df.iloc[-2]['close'] > df.iloc[-3]['close']:
                patterns.append(('THREE_WHITE_SOLDIERS', 4, 'Tres forte hausse'))

        # Three Black Crows
        if all(df.iloc[-i]['close'] < df.iloc[-i]['open'] for i in [1,2,3]):
            if df.iloc[-1]['close'] < df.iloc[-2]['close'] < df.iloc[-3]['close']:
                patterns.append(('THREE_BLACK_CROWS', -4, 'Tres forte baisse'))

        return patterns

    def multi_timeframe_bias(self, exchange, pair):
        """Biais directionnel multi-timeframe"""
        bias = 0
        tf_scores = {}
        for tf, weight in [('1m', 1), ('5m', 2), ('15m', 3)]:
            try:
                ohlcv = exchange.get_ohlcv(pair, timeframe=tf, limit=50)
                if ohlcv is None or len(ohlcv) < 20:
                    continue
                c = ohlcv['close']
                ema9  = c.ewm(span=9).mean().iloc[-1]
                ema21 = c.ewm(span=21).mean().iloc[-1]
                rsi   = self._fast_rsi(c, 14)
                score = 0
                if ema9 > ema21: score += 1
                else: score -= 1
                if rsi < 40: score += 1
                elif rsi > 60: score -= 1
                tf_scores[tf] = score
                bias += score * weight
            except:
                pass
        return bias, tf_scores

    def _fast_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / (loss + 0.0001)
        return float((100 - 100 / (1 + rs)).iloc[-1])

    def volume_analysis(self, df):
        """Analyse de volume"""
        score = 0; signals = []
        try:
            last = df.iloc[-1]; prev = df.iloc[-2]
            # Spike de volume sur mouvement haussier
            if last['vol_ratio'] > 2.0 and last['close'] > last['open']:
                score += 2; signals.append('VOL_SPIKE_BULL')
            elif last['vol_ratio'] > 2.0 and last['close'] < last['open']:
                score -= 2; signals.append('VOL_SPIKE_BEAR')
            # OBV trend
            if last['obv'] > last['obv_ema']: score += 1; signals.append('OBV_UP')
            else: score -= 1; signals.append('OBV_DOWN')
            # MFI
            if last['mfi'] < 20: score += 1.5; signals.append('MFI_OVERSOLD')
            elif last['mfi'] > 80: score -= 1.5; signals.append('MFI_OVERBOUGHT')
            # VWAP
            if last['close'] > last['vwap']: score += 0.5; signals.append('ABOVE_VWAP')
            else: score -= 0.5; signals.append('BELOW_VWAP')
        except: pass
        return score, signals

    def trend_analysis(self, df):
        """Analyse de tendance multi-indicateurs"""
        score = 0; signals = []
        try:
            last = df.iloc[-1]; prev = df.iloc[-2]
            c = last['close']

            # EMA stack (alignement haussier)
            if last.get('ema9',0) > last.get('ema21',0) > last.get('ema50',0):
                score += 3; signals.append('EMA_STACK_BULL')
            elif last.get('ema9',0) < last.get('ema21',0) < last.get('ema50',0):
                score -= 3; signals.append('EMA_STACK_BEAR')

            # EMA 9/21 croisement
            if last.get('ema9',0) > last.get('ema21',0) and prev.get('ema9',0) <= prev.get('ema21',0):
                score += 3; signals.append('EMA_CROSS_UP')
            elif last.get('ema9',0) < last.get('ema21',0) and prev.get('ema9',0) >= prev.get('ema21',0):
                score -= 3; signals.append('EMA_CROSS_DOWN')

            # Au-dessus / en-dessous EMA200
            if c > last.get('ema200', c): score += 1; signals.append('ABOVE_EMA200')
            else: score -= 1; signals.append('BELOW_EMA200')

            # Ichimoku
            sa = last.get('senkou_a', c); sb = last.get('senkou_b', c)
            cloud_top = max(sa, sb); cloud_bot = min(sa, sb)
            if c > cloud_top: score += 2; signals.append('ABOVE_CLOUD')
            elif c < cloud_bot: score -= 2; signals.append('BELOW_CLOUD')
            if last.get('tenkan',c) > last.get('kijun',c): score += 1; signals.append('TK_CROSS_UP')

            # Parabolic SAR
            if 'psar' in last.index:
                if c > last['psar']: score += 1; signals.append('PSAR_BULL')
                else: score -= 1; signals.append('PSAR_BEAR')

            # ADX force
            adx = last.get('adx', 0)
            if adx > 30:
                if last.get('adx_pos',0) > last.get('adx_neg',0): score += 2; signals.append('ADX_STRONG_UP')
                else: score -= 2; signals.append('ADX_STRONG_DOWN')

            # Aroon
            if last.get('aroon_osc',0) > 50: score += 1; signals.append('AROON_BULL')
            elif last.get('aroon_osc',0) < -50: score -= 1; signals.append('AROON_BEAR')

        except Exception as e:
            logger.error(f"trend_analysis error: {e}")
        return score, signals

    def momentum_analysis(self, df):
        """Analyse de momentum"""
        score = 0; signals = []
        try:
            last = df.iloc[-1]; prev = df.iloc[-2]

            # RSI multi
            rsi = last.get('rsi14', 50)
            if rsi < 30: score += 3; signals.append('RSI14_OVERSOLD')
            elif rsi < 40: score += 1.5; signals.append('RSI14_LOW')
            elif rsi > 70: score -= 3; signals.append('RSI14_OVERBOUGHT')
            elif rsi > 60: score -= 1.5; signals.append('RSI14_HIGH')

            # RSI divergence
            if rsi > prev.get('rsi14',50) and last['close'] > prev['close']: score += 0.5
            elif rsi < prev.get('rsi14',50) and last['close'] < prev['close']: score -= 0.5

            # MACD 3 versions
            for fast, slow in [(12,26),(5,13),(8,21)]:
                hist_key = f'macd_hist_{fast}_{slow}'
                if hist_key in df.columns:
                    h_last = last.get(hist_key, 0); h_prev = prev.get(hist_key, 0)
                    if h_last > 0 and h_prev <= 0: score += 2; signals.append(f'MACD{fast}_{slow}_CROSS_UP')
                    elif h_last < 0 and h_prev >= 0: score -= 2; signals.append(f'MACD{fast}_{slow}_CROSS_DOWN')
                    elif h_last > h_prev: score += 0.3
                    else: score -= 0.3

            # Stochastic
            k = last.get('stoch_k', 50); d = last.get('stoch_d', 50)
            pk = prev.get('stoch_k', 50)
            if k < 20 and k > pk: score += 2; signals.append('STOCH_OVERSOLD_CROSS')
            elif k > 80 and k < pk: score -= 2; signals.append('STOCH_OVERBOUGHT_CROSS')

            # CCI
            cci = last.get('cci', 0)
            if cci < -100: score += 1.5; signals.append('CCI_OVERSOLD')
            elif cci > 100: score -= 1.5; signals.append('CCI_OVERBOUGHT')

            # Williams %R
            wr = last.get('williams_r', -50)
            if wr < -80: score += 1; signals.append('WR_OVERSOLD')
            elif wr > -20: score -= 1; signals.append('WR_OVERBOUGHT')

            # ROC
            roc = last.get('roc', 0)
            if roc > 2: score += 0.5
            elif roc < -2: score -= 0.5

        except Exception as e:
            logger.error(f"momentum_analysis error: {e}")
        return score, signals

    def volatility_analysis(self, df):
        """Analyse de volatilite"""
        score = 0; signals = []
        try:
            last = df.iloc[-1]
            c = last['close']

            # Bollinger %B
            bp = last.get('bb_pct', 0.5)
            if bp < 0.05: score += 2; signals.append('BB_SQUEEZE_BOTTOM')
            elif bp > 0.95: score -= 2; signals.append('BB_SQUEEZE_TOP')
            elif 0.45 < bp < 0.55: signals.append('BB_MID')

            # Squeeze Momentum
            if last.get('squeeze', False): signals.append('SQUEEZE_ON')

            # ATR pour ajuster taille de position
            atr_pct = last.get('atr_pct', 1)
            if atr_pct < 0.3: signals.append('LOW_VOLATILITY')
            elif atr_pct > 2: signals.append('HIGH_VOLATILITY')

            # Support/Resistance
            s1 = last.get('s1', c * 0.99); r1 = last.get('r1', c * 1.01)
            if abs(c - s1) / c < 0.005: score += 1.5; signals.append('NEAR_SUPPORT')
            if abs(c - r1) / c < 0.005: score -= 1.5; signals.append('NEAR_RESISTANCE')

        except Exception as e:
            logger.error(f"volatility_analysis error: {e}")
        return score, signals


class TradingStrategy:
    def __init__(self):
        self.ml_model = None
        self.analyzer = MarketAnalyzer()
        self._exchange = None

    def set_ml_model(self, model):
        self.ml_model = model

    def set_exchange(self, exchange):
        self._exchange = exchange

    def compute_indicators(self, df):
        return self.analyzer.compute_all(df)

    def generate_signal(self, df, symbol=''):
        try:
            df = self.analyzer.compute_all(df.copy())
            df.dropna(subset=['ema9','rsi14'], inplace=True)
            if len(df) < 5:
                return self._hold()

            last = df.iloc[-1]

            # === VOTES par categorie ===
            trend_score,    trend_sigs    = self.analyzer.trend_analysis(df)
            momentum_score, momentum_sigs = self.analyzer.momentum_analysis(df)
            volume_score,   volume_sigs   = self.analyzer.volume_analysis(df)
            volatility_score, vol_sigs    = self.analyzer.volatility_analysis(df)
            patterns = self.analyzer.detect_patterns(df)
            pattern_score = sum(p[1] for p in patterns)
            pattern_sigs  = [p[0] for p in patterns]

            # Biais multi-timeframe
            mtf_score = 0
            mtf_info = {}
            if self._exchange:
                mtf_score, mtf_info = self.analyzer.multi_timeframe_bias(self._exchange, symbol)

            # === SCORE FINAL PONDERE ===
            total = (
                trend_score    * 2.5 +
                momentum_score * 2.0 +
                volume_score   * 1.5 +
                pattern_score  * 1.5 +
                mtf_score      * 2.0 +
                volatility_score * 0.5
            )

            # ML boost
            ml_boost = 0
            if self.ml_model and self.ml_model.is_trained:
                ml_sig = self.ml_model.predict(df)
                if ml_sig['action'] == 'BUY':   ml_boost = +3
                elif ml_sig['action'] == 'SELL': ml_boost = -3
                total += ml_boost

            # Confidence normalisee 0-1
            max_possible = 30.0
            confidence = min(abs(total) / max_possible, 1.0)

            # Decision
            if total > 4:
                action = 'BUY'
            elif total < -4:
                action = 'SELL'
            else:
                action = 'HOLD'

            all_signals = trend_sigs + momentum_sigs + volume_sigs + vol_sigs + pattern_sigs

            return {
                'action': action,
                'confidence': round(confidence, 3),
                'total_score': round(total, 2),
                'trend_score': round(trend_score, 2),
                'momentum_score': round(momentum_score, 2),
                'volume_score': round(volume_score, 2),
                'pattern_score': round(pattern_score, 2),
                'mtf_score': round(mtf_score, 2),
                'mtf_info': mtf_info,
                'signals': all_signals,
                'patterns': pattern_sigs,
                'rsi': round(float(last.get('rsi14', 50)), 1),
                'adx': round(float(last.get('adx', 0)), 1),
                'bb_pct': round(float(last.get('bb_pct', 0.5)), 3),
                'atr': round(float(last.get('atr', 0)), 4),
                'price': round(float(last['close']), 4)
            }

        except Exception as e:
            logger.error(f"generate_signal error ({symbol}): {e}")
            return self._hold()

    def _hold(self):
        return {'action': 'HOLD', 'confidence': 0, 'total_score': 0,
                'signals': [], 'patterns': [], 'rsi': 50, 'adx': 0,
                'bb_pct': 0.5, 'atr': 0, 'price': 0,
                'trend_score':0,'momentum_score':0,'volume_score':0,
                'pattern_score':0,'mtf_score':0,'mtf_info':{}}
