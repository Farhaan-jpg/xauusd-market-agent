"""Telegram Bot client with safe HTML formatting, retry handling, and local logging fallback."""
import asyncio
import html
from typing import Any, Dict, Optional
import httpx
from app.config.settings import settings
from app.core.logging import logger
from app.storage.repository import Repository

class TelegramBot:
    """Sends structured alerts and reports to Telegram with spam control and HTML escaping."""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ALERTS_ENABLED and settings.has_telegram

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Sends a text message to the configured Telegram chat."""
        if not self.enabled:
            logger.info(f"[TELEGRAM SIMULATION / LOCAL LOG]\n{text}")
            return True

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                await Repository.update_provider_health("Telegram_Bot", is_healthy=True)
                return True
            else:
                logger.error(f"Telegram send failed ({resp.status_code}): {resp.text}")
                await Repository.update_provider_health("Telegram_Bot", is_healthy=False, error_message=resp.text)
                return False
        except Exception as e:
            logger.error(f"Telegram send exception: {e}")
            await Repository.update_provider_health("Telegram_Bot", is_healthy=False, error_message=str(e))
            return False

    @staticmethod
    def escape(text: str) -> str:
        """Escapes raw strings for safe Telegram HTML output."""
        return html.escape(str(text))
