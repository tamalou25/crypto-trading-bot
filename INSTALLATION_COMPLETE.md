# 🚀 GUIDE D'INSTALLATION COMPLET - CRYPTO TRADING BOT

> **Bot de trading crypto automatisé avec IA, interface web temps réel, et sécurité renforcée**

---

## 📚 TABLE DES MATIÈRES

1. [Pré-requis](#pré-requis)
2. [Installation Locale](#installation-locale)
3. [Configuration Sécurisée](#configuration-sécurisée)
4. [Lancement du Bot](#lancement-du-bot)
5. [Interface Web](#interface-web)
6. [Déploiement 24/7](#déploiement-247)
7. [Sécurité Avancée](#sécurité-avancée)
8. [Résolution de Problèmes](#résolution-de-problèmes)
9. [FAQ](#faq)

---

## PRÉ-REQUIS

### Logiciels Nécessaires

**Windows:**
```powershell
# 1. Python 3.10+ (https://python.org)
winget install Python.Python.3.11

# 2. Git
winget install Git.Git

# 3. Vérifier l'installation
python --version
git --version
```

**macOS:**
```bash
# 1. Homebrew (si pas déjà installé)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python & Git
brew install python@3.11 git

# 3. Vérifier
python3 --version
git --version
```

**Linux (Ubuntu/Debian):**
```bash
# Mise à jour
sudo apt update && sudo apt upgrade -y

# Installation
sudo apt install -y python3.11 python3-pip python3-venv git

# Vérifier
python3 --version
git --version
```

### Compte Binance

1. Créer un compte sur [binance.com](https://binance.com)
2. Activer l'authentification 2FA (OBLIGATOIRE)
3. Compléter la vérification KYC (recommandé)

---

## INSTALLATION LOCALE

### Étape 1: Cloner le Projet

```bash
# Cloner le dépôt
git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot

# Vérifier que vous êtes dans le bon dossier
ls -la  # Linux/macOS
dir     # Windows
```

### Étape 2: Environnement Virtuel

**Linux/macOS:**
```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Votre terminal devrait maintenant afficher (venv) au début
```

**Windows:**
```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
venv\Scripts\activate

# Votre terminal devrait maintenant afficher (venv) au début
```

### Étape 3: Installer les Dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Installer toutes les dépendances
pip install -r requirements.txt

# Vérifier l'installation (devrait afficher la liste des packages)
pip list
```

**Si vous rencontrez des erreurs:**

```bash
# Pour les erreurs TA-Lib sur Windows:
pip install TA-Lib-0.4.28-cp311-cp311-win_amd64.whl

# Pour les erreurs TA-Lib sur macOS:
brew install ta-lib
pip install TA-Lib

# Pour les erreurs TA-Lib sur Linux:
sudo apt-get install ta-lib
pip install TA-Lib
```

---

## CONFIGURATION SÉCURISÉE

### Étape 1: Créer les API Keys Binance

**IMPORTANT: Suivez ces étapes EXACTEMENT pour la sécurité**

1. Connectez-vous sur [binance.com](https://binance.com)
2. Menu utilisateur (en haut à droite) → **API Management**
3. Cliquez sur **"Create API"**
4. Donnez un label: `Trading Bot Paper`
5. Authentification 2FA requise

**PERMISSIONS À ACTIVER (CRITIQUE):**

✅ **Enable Reading** (lecture des données)
✅ **Enable Spot & Margin Trading** (trading spot uniquement)

❌ **JAMAIS Enable Withdrawals** (retrait de fonds)
❌ **JAMAIS Enable Futures** (futures/leverage)

6. **IP Whitelist (FORTEMENT RECOMMANDÉ):**
   - Ajoutez l'IP de votre machine
   - Trouvez votre IP: [whatismyip.com](https://www.whatismyip.com)
   - Collez l'IP dans "Restrict access to trusted IPs"

7. Copiez les deux clés:
   - **API Key** (publique)
   - **Secret Key** (privée - NE JAMAIS PARTAGER)

### Étape 2: Configuration du Fichier .env

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer le fichier .env
nano .env    # Linux/macOS
notepad .env # Windows
```

**Contenu du .env (ADAPTER VOS VALEURS):**

```env
# === BINANCE API (OBLIGATOIRE) ===
BINANCE_API_KEY=votre_cle_api_ici
BINANCE_SECRET_KEY=votre_cle_secrete_ici

# === MODE DE TRADING (IMPORTANT!) ===
# paper = simulation SANS argent réel (COMMENCER ICI)
# live = argent réel (DANGER - seulement après tests)
TRADING_MODE=paper

# === CAPITAL INITIAL ===
INITIAL_CAPITAL=1000

# === PAIRES À TRADER ===
# Séparer par des virgules, pas d'espaces
TRADING_PAIRS=BTC/USDT,ETH/USDT,SOL/USDT

# === TIMEFRAME ===
TIMEFRAME=15m
FAST_TIMEFRAME=5m

# === GESTION DU RISQUE ===
STOP_LOSS_PCT=0.025        # -2.5% stop loss
TAKE_PROFIT_PCT=0.05       # +5% take profit
MAX_POSITION_SIZE=0.15     # 15% max du capital par trade
MAX_OPEN_TRADES=3          # 3 positions max simultanées
TRAILING_STOP=true         # Protection des gains

# === TELEGRAM (OPTIONNEL) ===
# Laisser vide si vous n'utilisez pas Telegram
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
```

**SAUVEGARDER LE FICHIER (Ctrl+O puis Ctrl+X sur nano)**

### Étape 3: Créer les Dossiers Nécessaires

```bash
# Créer automatiquement tous les dossiers
mkdir -p logs models data

# Vérifier
ls -la
```

---

## LANCEMENT DU BOT

### Étape 1: Backtest OBLIGATOIRE

**TOUJOURS commencer par un backtest avant le paper trading**

```bash
# Lancer le backtest sur données historiques
python backtest_run.py
```

**Analyser les résultats:**

```
📊 RÉSULTATS BACKTEST
 Trades: 42
 Gagnants: 26 (61.9%)
 Perdants: 16
 PnL Total: +78.34 USDT
 ROI: +7.83%
 Capital Final: 1078.34 USDT
```

✅ **Bon signe:** Win rate > 55%, ROI positif
❌ **Mauvais signe:** Win rate < 50%, ROI négatif → ajuster la stratégie

### Étape 2: Paper Trading

**Mode simulation SANS argent réel**

```bash
# Lancer le bot en mode paper
python bot.py
```

**Vous devriez voir:**

```
 ╔═══════════════════════════════════════╗
 ║     🤖 AI CRYPTO TRADING BOT 🤖       ║
 ║     github.com/tamalou25             ║
 ╚═══════════════════════════════════════╝

 Mode: PAPER
 Paires: BTC/USDT, ETH/USDT, SOL/USDT
 Capital: 1000 USDT

🧠 Chargement du modèle ML...
✅ Modèle ML chargé depuis disque
🚀 Bot démarré! Cycle toutes les 5 minutes
📊 Analyse de BTC/USDT...
Signal BTC/USDT: BUY (confiance: 0.72)
```

**Laisser tourner 1-2 semaines minimum pour valider la stratégie**

### Étape 3: Interface Web (Dashboard)

**Ouvrir un NOUVEAU terminal (garder le bot actif)**

```bash
# Dans le même dossier
cd crypto-trading-bot

# Activer l'environnement
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Ouvrir le navigateur sur le dashboard
# Le dashboard est déjà intégré dans bot.py
```

**Ouvrir dans votre navigateur:**
```
http://localhost:5000
```

OU utiliser l'interface web standalone:

```bash
# Lancer un serveur HTTP simple
cd web
python -m http.server 8080

# Ouvrir dans le navigateur:
# http://localhost:8080
```

**Le dashboard affiche:**
- Capital total en temps réel
- ROI et Win Rate
- Positions ouvertes
- Historique des trades
- PnL par trade

---

## DÉPLOIEMENT 24/7

### Option 1: VPS Cloud (Recommandé)

**Pourquoi un VPS?**
- Tourne 24/7 sans interruption
- Pas besoin de laisser votre PC allumé
- Latence minimale vers Binance
- Backup automatique

**Fournisseurs recommandés:**

| Provider | Prix | Specs | Avantages |
|----------|------|-------|----------|
| **DigitalOcean** | 4$/mois | 1 CPU, 1GB RAM | Interface simple |
| **OVH VPS Starter** | 3.50€/mois | 1 vCore, 2GB RAM | Serveurs EU |
| **Contabo** | 4€/mois | 4 vCores, 8GB RAM | Meilleur rapport qualité/prix |
| **Oracle Cloud Free** | GRATUIT | 1 CPU, 1GB RAM | Free tier permanent |

**Installation sur VPS Ubuntu:**

```bash
# 1. Se connecter au VPS
ssh root@votre_ip_vps

# 2. Installer les dépendances
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip python3-venv git screen

# 3. Cloner le projet
git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot

# 4. Setup environnement
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configurer .env
nano .env
# (coller votre config)

# 6. Lancer avec screen (persiste même après déconnexion)
screen -S bot
python bot.py

# 7. Détacher screen (bot continue en arrière-plan)
# Appuyer sur: Ctrl+A puis D

# 8. Revenir au bot plus tard
screen -r bot
```

### Option 2: Docker (Avancé)

```bash
# Créer un Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
EOF

# Build & Run
docker build -t crypto-bot .
docker run -d --name trading-bot --env-file .env crypto-bot

# Voir les logs
docker logs -f trading-bot
```

### Option 3: systemd Service (Linux)

```bash
# Créer un service systemd
sudo nano /etc/systemd/system/crypto-bot.service
```

**Contenu du fichier:**

```ini
[Unit]
Description=Crypto Trading Bot
After=network.target

[Service]
Type=simple
User=votre_utilisateur
WorkingDirectory=/chemin/vers/crypto-trading-bot
Environment="PATH=/chemin/vers/crypto-trading-bot/venv/bin"
ExecStart=/chemin/vers/crypto-trading-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot

# Vérifier le statut
sudo systemctl status crypto-bot

# Voir les logs
sudo journalctl -u crypto-bot -f
```

---

## SÉCURITÉ AVANCÉE

### 1. Protection des Clés API

```bash
# Permissions strictes sur .env
chmod 600 .env

# Vérifier
ls -la .env
# Devrait afficher: -rw------- (lisible uniquement par vous)
```

### 2. Rotation des API Keys

**Changer vos clés tous les 30 jours:**

1. Créer une nouvelle API key sur Binance
2. Mettre à jour `.env` avec les nouvelles clés
3. Redémarrer le bot
4. Supprimer l'ancienne API key sur Binance

### 3. Monitoring & Alertes

**Configurer Telegram (optionnel mais recommandé):**

```bash
# 1. Créer un bot Telegram
# Ouvrir Telegram → chercher @BotFather
# Taper: /newbot
# Suivre les instructions → récupérer le TOKEN

# 2. Obtenir votre Chat ID
# Chercher @userinfobot sur Telegram
# Envoyer un message → récupérer votre ID

# 3. Mettre à jour .env
TELEGRAM_TOKEN=votre_token_ici
TELEGRAM_CHAT_ID=votre_chat_id_ici
```

**Vous recevrez des notifications pour:**
- Ouverture de positions
- Fermeture de positions (TP/SL)
- Erreurs critiques
- Démarrage/arrêt du bot

### 4. Firewall Configuration (VPS)

```bash
# Installer UFW (Uncomplicated Firewall)
sudo apt install ufw

# Autoriser SSH uniquement
sudo ufw allow 22/tcp

# Autoriser dashboard (optionnel - seulement si accès distant)
sudo ufw allow 5000/tcp

# Activer le firewall
sudo ufw enable

# Vérifier
sudo ufw status
```

### 5. Limitation de Débit (Rate Limiting)

**Déjà configuré dans le code:**

```python
# src/exchange.py
self.exchange = ccxt.binance({
    'enableRateLimit': True,  # ✅ Protection anti-ban
    'rateLimit': 1200         # 1 requête par 1.2 secondes max
})
```

---

## RÉSOLUTION DE PROBLÈMES

### Erreur: "Module 'ccxt' not found"

```bash
# Vérifier que l'environnement virtuel est activé
which python  # Doit pointer vers venv/bin/python

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur: "API key invalid"

```bash
# Vérifier les clés API
cat .env | grep BINANCE

# Pas d'espaces autour du =
# Pas de guillemets autour des clés
# Format correct:
BINANCE_API_KEY=abc123def456
BINANCE_SECRET_KEY=xyz789uvw
```

### Erreur: "Permission denied" sur .env

```bash
# Linux/macOS
chmod 600 .env

# Windows
# Clic droit → Propriétés → Sécurité → Modifier
```

### Bot ne trade pas

**Vérifier:**

1. Mode paper activé? `TRADING_MODE=paper` dans `.env`
2. Paires correctes? Vérifier `TRADING_PAIRS` format: `BTC/USDT,ETH/USDT`
3. Capital suffisant? Minimum 100 USDT recommandé
4. Logs d'erreur?

```bash
# Voir les logs détaillés
tail -f logs/bot.log
```

### Dashboard ne charge pas

```bash
# Vérifier que le bot tourne
ps aux | grep bot.py

# Vérifier le port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Essayer avec l'interface standalone
cd web
python -m http.server 8080
# Ouvrir http://localhost:8080
```

---

## FAQ

### Q: Combien de capital minimum pour commencer?

**A:** En paper trading: aucun (simulation). En live: minimum 100-200€ recommandé. Commencez TOUJOURS en paper.

### Q: Combien de temps pour être rentable?

**A:** Variable. En moyenne:
- 2-4 semaines de paper trading pour valider
- 1-3 mois de live trading avec petit capital
- 6-12 mois pour optimiser et scaler

### Q: Puis-je trader autre chose que crypto?

**A:** Le bot utilise CCXT qui supporte 100+ exchanges. Mais le code est optimisé pour crypto. Pour forex/actions, utilisez MT5 ou Interactive Brokers.

### Q: Le bot peut-il perdre tout mon argent?

**A:** Oui, si mal configuré. **C'EST POURQUOI:**
- ✅ Toujours tester en paper 2+ semaines
- ✅ Commencer avec 100-200€ MAX en live
- ✅ Utiliser Stop-Loss (configuré par défaut)
- ✅ Jamais plus de 15% du capital par trade
- ✅ Max 3 positions simultanées

### Q: Puis-je utiliser plusieurs bots en même temps?

**A:** Oui, mais:
- Utilisez des API keys différentes
- Ou séparez les paires (Bot1: BTC/ETH, Bot2: SOL/BNB)
- Surveillez le capital total

### Q: Comment changer la stratégie?

**A:** Éditez `src/strategy.py`:

```python
# Modifier les paramètres RSI
if row['rsi'] < 30:  # Plus agressif: 35, conservateur: 25
    score += 2

# Ajouter un indicateur
from ta.momentum import StochRSI
df['stoch_rsi'] = StochRSI(df['close']).stochrsi()
```

Toujours backtester après modifications!

### Q: Le bot fonctionne-t-il sur Raspberry Pi?

**A:** Oui! Installation identique:

```bash
sudo apt install python3-pip git
git clone https://github.com/tamalou25/crypto-trading-bot.git
cd crypto-trading-bot
pip3 install -r requirements.txt
python3 bot.py
```

### Q: Puis-je vendre ce bot?

**A:** Le code est open-source (GPLv3). Vous pouvez:
- ✅ L'utiliser commercialement
- ✅ Le modifier
- ✅ Proposer des services de configuration
- ❌ Le vendre en fermant le code source

---

## 📞 SUPPORT

**Problèmes? Questions?**

1. Vérifier les [Issues GitHub](https://github.com/tamalou25/crypto-trading-bot/issues)
2. Créer une nouvelle issue avec:
   - Logs d'erreur
   - Configuration (SANS les clés API!)
   - OS et version Python

**Contributions bienvenues:**
- Fork le projet
- Créer une branche: `git checkout -b feature/amelioration`
- Commit: `git commit -m 'Ajout nouvelle feature'`
- Push: `git push origin feature/amelioration`
- Créer une Pull Request

---

**⚠️ DISCLAIMER LÉGAL**

Ce bot est fourni à des fins éducatives. Le trading comporte des risques importants de perte en capital. Les performances passées ne garantissent pas les résultats futurs. Tradez uniquement avec de l'argent que vous pouvez vous permettre de perdre. L'auteur ne peut être tenu responsable de vos pertes.
