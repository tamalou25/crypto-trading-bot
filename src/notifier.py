import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.enabled = bool(self.token and self.chat_id)
        if self.enabled:
            logger.info("📱 Telegram activé")
        else:
            logger.info("📱 Telegram désactivé (optionnel)")
    
    def send(self, message):
        if not self.enabled:
            logger.info(f"[NOTIF] {message}")
            return
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {'chat_id': self.chat_id, 'text': f"🤖 CryptoBot\n{message}", 'parse_mode': 'HTML'}
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.debug("Notification Telegram envoyée")
            else:
                logger.warning(f"Telegram error: {response.status_code}")
        except Exception as e:
            logger.error(f"Erreur Telegram: {e}")
