"""
Telegram Notification Service
"""
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self._bot_token = None
        self._default_chat_id = None
    
    @property
    def bot_token(self):
        if self._bot_token is None:
            from config import settings
            self._bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        return self._bot_token
    
    @property
    def default_chat_id(self):
        if self._default_chat_id is None:
            from config import settings
            self._default_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        return self._default_chat_id
    
    @property
    def base_url(self):
        return f"https://api.telegram.org/bot{self.bot_token}"
    
    async def _send_message(self, text: str, chat_id: str = None) -> Dict:
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return {'ok': False, 'error': 'Bot token not configured'}
        
        chat_id = chat_id or self.default_chat_id
        if not chat_id:
            return {'ok': False, 'error': 'Chat ID not configured'}
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {'ok': False, 'error': str(e)}
    
    async def send_signal_alert(self, prediction: Dict, chat_id: str = None) -> Dict:
        """Yeni sinyal bildirimi"""
        emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(prediction.get('direction'), '⚪')
        
        targets_text = ""
        if prediction.get('targets'):
            t = prediction['targets']
            targets_text = f"""
🎯 <b>Targets:</b>
  TP1: {t.get('tp1_price', 'N/A')} ({t.get('tp1_pips', '')} pips)
  TP2: {t.get('tp2_price', 'N/A')} ({t.get('tp2_pips', '')} pips)
  TP3: {t.get('tp3_price', 'N/A')} ({t.get('tp3_pips', '')} pips)
🛑 SL: {t.get('sl_price', 'N/A')} ({t.get('sl_pips', '')} pips)"""
        
        message = f"""
{emoji} <b>YENİ SİNYAL - {prediction.get('strategy', 'BALANCED').upper()}</b>

💎 Symbol: <b>{prediction.get('symbol')}</b>
📊 Direction: <b>{prediction.get('direction')}</b>
🎯 Entry: <b>{prediction.get('entry_price')}</b>
⭐ Confidence: <b>{prediction.get('confidence')}%</b>
{targets_text}

💡 {prediction.get('reasoning', ['N/A'])[0] if prediction.get('reasoning') else 'N/A'}
⏱️ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        return await self._send_message(message.strip(), chat_id)
    
    async def send_target_hit(self, symbol: str, target_level: str, pips: float, 
                              profit: float = 0, chat_id: str = None) -> Dict:
        """Target hit bildirimi"""
        emoji = '✅' if not target_level.startswith('SL') else '❌'
        message = f"""
{emoji} <b>TARGET HİT - {target_level}</b>

💎 Symbol: <b>{symbol}</b>
🎯 {target_level}: <b>{pips:+.1f} pips</b>
💰 Kar/Zarar: <b>${profit:+.2f}</b>

⏱️ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        return await self._send_message(message.strip(), chat_id)
    
    async def send_stop_loss(self, symbol: str, pips: float, loss: float = 0, 
                             chat_id: str = None) -> Dict:
        """Stop Loss bildirimi"""
        message = f"""
❌ <b>STOP LOSS</b>

💎 Symbol: <b>{symbol}</b>
🛑 SL: <b>{pips:.1f} pips</b>
💸 Zarar: <b>${loss:.2f}</b>

⏱️ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
        return await self._send_message(message.strip(), chat_id)
    
    async def send_market_alert(self, alert_type: str, message: str, 
                                chat_id: str = None) -> Dict:
        """Piyasa uyarısı"""
        text = f"⚠️ <b>{alert_type}</b>\n\n{message}"
        return await self._send_message(text, chat_id)
    
    async def test_connection(self, chat_id: str = None) -> Dict:
        """Test bildirimi"""
        message = "🔔 <b>ForexsAI Bildirim Testi</b>\n\nBağlantı başarılı! ✅"
        return await self._send_message(message, chat_id)


telegram_notifier = TelegramNotifier()
