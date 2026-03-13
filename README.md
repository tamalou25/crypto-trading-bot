# 🤖 AI Crypto Trading Bot

> Bot de trading automatique court-terme sur crypto avec signaux ML et interface web

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Objectif

Ce bot de trading crypto combine **analyse technique multi-indicateurs** et **Machine Learning** pour générer des signaux de trading court-terme optimisés avec:

- ✅ **Stratégie hybride** (RSI, MACD, EMA, Bollinger Bands, ADX + ML)
- ✅ **Gestion du risque automatique** (Stop-Loss / Take-Profit / Trailing Stop)
- ✅ **Interface web temps réel** pour monitoring
- ✅ **Paper trading** (simulation sans argent réel)
- ✅ **Sécurité renforcée** (API restrictions, encryption, monitoring)
- ✅ **Backtesting intégré** pour validation de stratégie

## 🚀 Quick Start

### Installation en 3 étapes:

```bash
# 1. Cloner le projet
git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer
cp .env.example .env
# Éditer .env avec vos clés API Binance

# 4. Lancer en mode paper trading
python bot.py
```

### Interface Web:

Ouvrir dans votre navigateur:
- **Dashboard intégré:** `http://localhost:5000`
- **Interface standalone:** `cd web && python -m http.server 8080`

## 📚 Documentation Complète

**LIRE IMPÉRATIVEMENT AVANT DE LANCER:**

- **[INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)** - Guide d'installation détaillé pas à pas
- **[SECURITE.md](SECURITE.md)** - Meilleures pratiques de sécurité

## ⚡ Features

### Analyse Technique
- RSI (Relative Strength Index) - 7 & 14 périodes
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Averages) - 9, 21, 50, 200
- Bollinger Bands - volatilité
- Stochastique - momentum
- ADX (Average Directional Index) - force de tendance
- ATR (Average True Range) - volatilité

### Machine Learning
- Gradient Boosting Classifier
- Features engineering (15+ indicateurs)
- Entraînement sur données historiques
- Prédiction de probabilité de hausse
- Fusion avec signaux techniques

### Gestion du Risque
- Stop-Loss: -2.5% (configurable)
- Take-Profit: +5% (configurable)
- Trailing Stop: protection des gains
- Position sizing: 15% max du capital par trade
- Max 3 positions simultanées

### Interface Web
- Capital total en temps réel
- ROI & Win Rate
- Positions ouvertes avec PnL
- Historique des 20 derniers trades
- Métriques de performance
- Auto-refresh toutes les 5 secondes

## 🔧 Architecture

```
crypto-trading-bot/
├── bot.py                 # Point d'entrée principal
├── backtest_run.py        # Backtesting sur données historiques
├── requirements.txt       # Dépendances Python
├── .env.example          # Template de configuration
├── web/
│   └── index.html        # Interface web standalone
├── src/
│   ├── exchange.py       # Client Binance (CCXT)
│   ├── strategy.py       # Stratégie de trading
│   ├── ml_model.py       # Modèle ML (Gradient Boosting)
│   ├── risk_manager.py   # Gestion SL/TP
│   ├── portfolio.py      # Gestion du portefeuille
│   ├── dashboard.py      # API Flask pour dashboard
│   ├── notifier.py       # Alertes Telegram
│   └── backtest.py       # Engine de backtesting
├── logs/                 # Logs du bot
├── models/               # Modèles ML sauvegardés
└── data/                 # Données historiques
```

## ⚙️ Configuration

### Fichier .env:

```env
# API Binance
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret

# Mode (TOUJOURS commencer en paper!)
TRADING_MODE=paper  # ou 'live'

# Capital & Paires
INITIAL_CAPITAL=1000
TRADING_PAIRS=BTC/USDT,ETH/USDT,SOL/USDT

# Risque
STOP_LOSS_PCT=0.025        # -2.5%
TAKE_PROFIT_PCT=0.05       # +5%
MAX_POSITION_SIZE=0.15     # 15% max
MAX_OPEN_TRADES=3
TRAILING_STOP=true

# Telegram (optionnel)
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
```

### Créer les API Keys Binance:

**IMPORTANT - Permissions de sécurité:**

✅ **Activer:**
- Enable Reading
- Enable Spot & Margin Trading
- IP Whitelist (recommandé)

❌ **NE JAMAIS activer:**
- Enable Withdrawals
- Enable Futures

[Guide détaillé](INSTALLATION_COMPLETE.md#configuration-sécurisée)

## 📊 Backtesting

TOUJOURS tester avant de passer en live:

```bash
python backtest_run.py
```

**Résultats attendus:**

```
📊 RÉSULTATS BACKTEST
 Trades: 42
 Gagnants: 26 (61.9%)
 Perdants: 16
 PnL Total: +78.34 USDT
 ROI: +7.83%
 Capital Final: 1078.34 USDT
 Meilleur trade: +12.45 USDT
 Pire trade: -5.23 USDT
```

## 🛡️ Sécurité

### Checklist de sécurité:

- [ ] API Keys sans permission de retrait
- [ ] IP Whitelist configurée
- [ ] Fichier .env avec permissions 600
- [ ] Rotation des clés tous les 30 jours
- [ ] Monitoring actif (Telegram)
- [ ] Backups automatiques
- [ ] Firewall configuré (VPS)

[Guide complet de sécurité](SECURITE.md)

## 💻 Déploiement 24/7

### Option 1: VPS Cloud

```bash
# Installation sur Ubuntu VPS
ssh root@your_vps_ip
apt update && apt upgrade -y
apt install -y python3.11 python3-pip git screen

git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot
pip install -r requirements.txt

# Configuration
nano .env

# Lancement persistant
screen -S bot
python bot.py
# Ctrl+A puis D pour détacher
```

### Option 2: Docker

```bash
docker build -t crypto-bot .
docker run -d --name trading-bot --env-file .env crypto-bot
docker logs -f trading-bot
```

[Guide déploiement complet](INSTALLATION_COMPLETE.md#déploiement-247)

## 📈 Performances Attendues

**Disclaimer:** Les performances passées ne garantissent pas les résultats futurs.

**Objectifs réalistes:**

| Période | ROI Attendu | Win Rate |
|---------|-------------|----------|
| 1 mois | 3-8% | 55-65% |
| 3 mois | 10-25% | 55-65% |
| 6 mois | 20-50% | 55-65% |

**Facteurs de succès:**
- Backtesting validé (>55% win rate)
- Paper trading 2+ semaines
- Discipline (ne pas modifier la stratégie en cours)
- Capital minimum 500-1000 USDT
- Surveillance régulière

## ⚠️ Avertissements

**LE TRADING COMPORTE DES RISQUES:**

- 🛑 Vous pouvez perdre tout votre capital
- 🛑 Commencez TOUJOURS en paper trading
- 🛑 Ne tradez que ce que vous pouvez perdre
- 🛑 Les marchés crypto sont extrêmement volatils
- 🛑 Aucune garantie de profit

**Ce bot est fourni à des fins éducatives. L'auteur ne peut être tenu responsable de vos pertes.**

## 👥 Support & Contributions

**Problèmes?**
- Vérifier [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)
- Consulter les [Issues GitHub](https://github.com/tamalou25/crypto-trading-bot/issues)
- Créer une nouvelle issue avec logs + config

**Contributions bienvenues:**
```bash
git checkout -b feature/nouvelle-feature
git commit -m 'Ajout feature X'
git push origin feature/nouvelle-feature
# Créer une Pull Request
```

## 📜 Licence

GPL-3.0 - Voir [LICENSE](LICENSE)

## 🚀 Roadmap

- [x] Stratégie technique de base
- [x] Modèle ML Gradient Boosting
- [x] Interface web temps réel
- [x] Paper trading
- [x] Backtesting
- [ ] Multi-exchange support (Coinbase, Kraken)
- [ ] Stratégies personnalisables via GUI
- [ ] Optimisation hyperparamètres automatique
- [ ] Trading de futures (avec levier)
- [ ] Portfolio rebalancing automatique

---

**Fait avec ❤️ par [tamalou25](https://github.com/tamalou25)**

**⭐ Star le projet si utile!**
