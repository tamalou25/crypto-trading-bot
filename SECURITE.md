# 🔒 GUIDE DE SÉCURITÉ - CRYPTO TRADING BOT

> **Protégez votre capital et vos données avec ces meilleures pratiques**

---

## 🚨 RÈGLES D'OR DE SÉCURITÉ

### 1. Protection des Clés API

**⚠️ CRITIQUE: Vos clés API = accès à votre argent**

#### Lors de la création des API Keys Binance:

✅ **À FAIRE:**
- Activer **Enable Reading**
- Activer **Enable Spot & Margin Trading**
- Configurer **IP Whitelist** (FORTEMENT recommandé)
- Utiliser l'authentification 2FA
- Donner un nom descriptif (ex: "Bot Paper Trading")

❌ **NE JAMAIS:**
- Activer **Enable Withdrawals** (retrait de fonds)
- Activer **Enable Futures** (trading à effet de levier)
- Partager vos clés API avec quiconque
- Copier vos clés dans des forums/Discord/Telegram
- Commit vos clés dans Git

#### Protection du fichier .env:

```bash
# Permissions strictes (Linux/macOS)
chmod 600 .env

# Vérifier
ls -la .env
# Doit afficher: -rw------- (lisible uniquement par vous)

# Ajouter .env au .gitignore
echo ".env" >> .gitignore
```

**Windows:**
```powershell
# Clic droit sur .env → Propriétés → Sécurité
# Supprimer tous les utilisateurs sauf le vôtre
# Donner uniquement "Lecture" et "Écriture"
```

---

### 2. IP Whitelisting (HAUTEMENT RECOMMANDÉ)

**Pourquoi?** Même si quelqu'un vole vos clés API, il ne pourra pas les utiliser sans votre IP.

#### Configuration:

1. **Trouver votre IP publique:**
   - [whatismyip.com](https://www.whatismyip.com)
   - Ou dans le terminal: `curl ifconfig.me`

2. **Sur Binance API Management:**
   - "Restrict access to trusted IPs"
   - Ajouter votre IP (ex: `203.0.113.45`)
   - Pour un VPS: ajouter l'IP du VPS

3. **IP dynamique?** (change régulièrement)
   - Option A: Utiliser un VPS avec IP fixe
   - Option B: Mettre à jour l'IP whitelist quand elle change
   - Option C: Ne pas utiliser whitelist (moins sécurisé)

**⚠️ Attention:** Si vous whitelistez votre IP et qu'elle change, le bot ne pourra plus trader.

---

### 3. Rotation Régulière des Clés

**Fréquence recommandée: tous les 30 jours**

```bash
# Procédure de rotation:

# 1. Créer une nouvelle API key sur Binance
#    (avec les mêmes permissions que l'ancienne)

# 2. Mettre à jour .env
nano .env
# Remplacer BINANCE_API_KEY et BINANCE_SECRET_KEY

# 3. Redémarrer le bot
pkill -f bot.py
python bot.py

# 4. Vérifier que tout fonctionne (5-10 minutes)

# 5. Supprimer l'ancienne API key sur Binance
```

**Créer un rappel mensuel:**
```bash
# Linux/macOS avec cron
crontab -e
# Ajouter:
0 9 1 * * echo "Rotation API Keys Binance aujourd'hui!" | mail -s "Reminder" votre@email.com
```

---

### 4. Gestion du Risque

#### Configuration Recommandée (.env):

```env
# Capital maximum par position: 15%
MAX_POSITION_SIZE=0.15

# Positions simultanées max: 3
MAX_OPEN_TRADES=3

# Stop-Loss: -2.5% (ajuster selon votre tolérance)
STOP_LOSS_PCT=0.025

# Take-Profit: +5%
TAKE_PROFIT_PCT=0.05

# Trailing Stop: protège les gains
TRAILING_STOP=true
```

**Calcul du risque total:**

```
Risque max par trade = Capital × MAX_POSITION_SIZE × STOP_LOSS_PCT
Risque max simultané = Risque par trade × MAX_OPEN_TRADES

Exemple avec 1000€:
- Risque par trade = 1000 × 0.15 × 0.025 = 3.75€
- Risque max total = 3.75 × 3 = 11.25€ (1.125% du capital)
```

#### Règles de Drawdown:

```python
# Ajouter dans src/risk_manager.py (optionnel)

class RiskManager:
    def __init__(self):
        # ...
        self.max_daily_loss_pct = 0.05  # -5% max par jour
        self.daily_start_balance = None
    
    def check_daily_drawdown(self, portfolio):
        if self.daily_start_balance is None:
            self.daily_start_balance = portfolio.get_total_value()
        
        current = portfolio.get_total_value()
        daily_loss = (self.daily_start_balance - current) / self.daily_start_balance
        
        if daily_loss >= self.max_daily_loss_pct:
            logger.critical(f"⛔ DRAWDOWN LIMITE ATTEINT: {daily_loss*100:.2f}%")
            return False  # Stopper le trading
        return True
```

---

### 5. Monitoring & Alertes

#### Configuration Telegram (Recommandé):

**Pourquoi?** Recevoir des notifications instantanées sur votre téléphone.

```bash
# 1. Créer un bot Telegram
# Ouvrir Telegram → @BotFather → /newbot
# Nom: "Crypto Trading Bot Alerts"
# Username: "votrenom_tradingbot"
# Copier le TOKEN

# 2. Obtenir votre Chat ID
# @userinfobot → Start → copier l'ID

# 3. Mettre à jour .env
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# 4. Tester
python -c "from src.notifier import TelegramNotifier; TelegramNotifier().send('Test OK!')"
```

**Notifications envoyées:**
- 🟢 Ouverture de position
- 🔴 Fermeture de position (TP/SL)
- ⚠️ Erreurs critiques
- 🚀 Démarrage/arrêt du bot
- 🚨 Drawdown limite atteint

#### Logs Structurés:

```bash
# Les logs sont automatiquement écrits dans logs/bot.log

# Voir en temps réel
tail -f logs/bot.log

# Filtrer les erreurs
grep ERROR logs/bot.log

# Dernières 100 lignes
tail -n 100 logs/bot.log

# Archiver les vieux logs (tous les mois)
tar -czf logs/archive_$(date +%Y%m).tar.gz logs/bot.log
> logs/bot.log  # Vider le fichier
```

---

### 6. Sécurité Réseau (VPS)

#### Firewall Configuration:

```bash
# Installer UFW
sudo apt install ufw

# Règles par défaut
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Autoriser SSH (ATTENTION: vérifier le port avant!)
sudo ufw allow 22/tcp

# Autoriser dashboard (si accès distant nécessaire)
sudo ufw allow 5000/tcp

# Activer
sudo ufw enable

# Vérifier
sudo ufw status verbose
```

#### SSH Sécurisé:

```bash
# Éditer la config SSH
sudo nano /etc/ssh/sshd_config

# Modifier:
Port 2222  # Changer le port par défaut
PermitRootLogin no  # Interdire root
PasswordAuthentication no  # Uniquement clés SSH

# Redémarrer SSH
sudo systemctl restart sshd

# Mettre à jour le firewall
sudo ufw delete allow 22/tcp
sudo ufw allow 2222/tcp
```

#### Fail2Ban (anti brute-force):

```bash
# Installer
sudo apt install fail2ban

# Configurer
sudo nano /etc/fail2ban/jail.local

# Ajouter:
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

# Redémarrer
sudo systemctl restart fail2ban

# Vérifier
sudo fail2ban-client status sshd
```

---

### 7. Backup & Récupération

#### Sauvegarde Automatique:

```bash
# Script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$HOME/backups"
mkdir -p $BACKUP_DIR

# Backup des fichiers critiques
tar -czf $BACKUP_DIR/bot_backup_$DATE.tar.gz \
    .env \
    src/ \
    models/ \
    logs/ \
    data/ \
    --exclude='*.pyc' \
    --exclude='__pycache__'

echo "Backup créé: bot_backup_$DATE.tar.gz"

# Garder seulement les 7 derniers backups
cd $BACKUP_DIR
ls -t | tail -n +8 | xargs rm -f
EOF

chmod +x backup.sh

# Automatiser avec cron (tous les jours à 3h du matin)
crontab -e
# Ajouter:
0 3 * * * /chemin/vers/crypto-trading-bot/backup.sh
```

#### Restauration:

```bash
# Lister les backups
ls -lh ~/backups/

# Restaurer
tar -xzf ~/backups/bot_backup_20260313_030000.tar.gz
```

---

### 8. Audits de Sécurité

#### Checklist Hebdomadaire:

```bash
# 1. Vérifier les logs pour activités suspectes
grep -i "error\|fail\|unauthorized" logs/bot.log | tail -n 50

# 2. Vérifier les trades sur Binance
# Comparer avec l'historique local

# 3. Vérifier les connexions API sur Binance
# Account → API Management → voir l'activité

# 4. Vérifier l'état du système (VPS)
top
df -h
free -m

# 5. Vérifier les mises à jour de sécurité
sudo apt update
sudo apt list --upgradable
```

#### Checklist Mensuelle:

- [ ] Rotation des API Keys
- [ ] Mise à jour des dépendances Python
- [ ] Review du code des nouvelles features
- [ ] Test de restauration backup
- [ ] Vérification des permissions fichiers
- [ ] Audit des stratégies de trading

```bash
# Mettre à jour les dépendances
pip list --outdated
pip install --upgrade ccxt pandas numpy scikit-learn

# Vérifier les vulnérabilités
pip install safety
safety check
```

---

### 9. Isolation & Sandboxing

#### Environnement Virtuel Strict:

```bash
# Toujours utiliser un venv dédié
python3 -m venv venv
source venv/bin/activate

# Vérifier qu'on est bien dans le venv
which python
# Doit afficher: /chemin/vers/crypto-trading-bot/venv/bin/python

# Ne JAMAIS installer globalement
pip install -r requirements.txt  # ✅
sudo pip install -r requirements.txt  # ❌ JAMAIS
```

#### Docker (Isolation Complète):

```dockerfile
# Dockerfile avec sécurité renforcée
FROM python:3.11-slim

# Créer un utilisateur non-root
RUN useradd -m -u 1000 botuser

WORKDIR /app

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY --chown=botuser:botuser . .

# Permissions strictes
RUN chmod 600 .env

# Switcher vers utilisateur non-root
USER botuser

CMD ["python", "bot.py"]
```

```bash
# Build
docker build -t crypto-bot:secure .

# Run avec sécurité
docker run -d \
    --name trading-bot \
    --read-only \
    --security-opt=no-new-privileges \
    --cap-drop=ALL \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    --env-file .env \
    crypto-bot:secure
```

---

### 10. Conformité Légale

#### KYC/AML:

- ✅ Compléter la vérification KYC sur Binance
- ✅ Respecter les limites de trading selon votre pays
- ✅ Garder des enregistrements de tous les trades
- ✅ Déclarer les gains aux impôts

#### Taxes:

```bash
# Exporter l'historique pour la déclaration fiscale
python -c "
from src.portfolio import Portfolio
import json

p = Portfolio()
with open('trade_history_2026.json', 'w') as f:
    json.dump(p.trade_history, f, indent=2, default=str)
print('Historique exporté: trade_history_2026.json')
"

# Format CSV pour Excel
python -c "
import pandas as pd
import json

with open('trade_history_2026.json') as f:
    data = json.load(f)

df = pd.DataFrame(data)
df.to_csv('trades_2026.csv', index=False)
print('CSV créé: trades_2026.csv')
"
```

---

## 🚨 EN CAS DE COMPROMISSION

### Si vous pensez que vos clés API ont été volées:

**AGIR IMMÉDIATEMENT:**

1. **Supprimer les API Keys sur Binance**
   - Se connecter sur binance.com
   - API Management → Supprimer TOUTES les clés

2. **Vérifier l'activité récente**
   - Spot Wallet → Transaction History
   - Chercher des trades suspects

3. **Changer le mot de passe Binance**
   - Utiliser un mot de passe unique et fort
   - Min 16 caractères, majuscules, chiffres, symboles

4. **Activer/Réactiver 2FA**
   - Google Authenticator ou Authy (pas SMS)

5. **Vérifier les withdrawals whitelists**
   - Security → Withdrawal Whitelist
   - Activer si pas déjà fait

6. **Contacter le support Binance**
   - Si des fonds ont été retirés
   - Fournir les détails de l'incident

7. **Scanner votre machine**
   - Antivirus/Antimalware complet
   - Vérifier les keyloggers

8. **Créer de nouvelles clés API**
   - Avec IP whitelist cette fois
   - Permissions minimales

---

## 📚 RESSOURCES COMPLÉMENTAIRES

### Documentation Officielle:

- [Binance API Security](https://www.binance.com/en/support/faq/360002502072)
- [CCXT Security Best Practices](https://github.com/ccxt/ccxt/wiki/Manual#authentication)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

### Outils de Sécurité:

```bash
# Scanner de vulnérabilités Python
pip install bandit
bandit -r src/

# Vérifier les secrets dans le code
pip install detect-secrets
detect-secrets scan

# Audit des dépendances
pip install pip-audit
pip-audit
```

---

**⚠️ La sécurité est un processus continu, pas un état final. Restez vigilant!**
