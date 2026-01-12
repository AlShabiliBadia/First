import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import settings


class DiscordAlertHandler(logging.Handler):
    """
    Custom logging handler that sends CRITICAL logs to Discord webhook.

    """
    
    def __init__(self, webhook_url: str):
        super().__init__(level=logging.CRITICAL)
        self.webhook_url = webhook_url
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to Discord."""
        if not self.webhook_url:
            return
            
        try:
            payload = self._format_discord_payload(record)
            
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._send_to_discord(payload))
            except RuntimeError:
                asyncio.run(self._send_to_discord(payload))
                
        except Exception:
            self.handleError(record)
    
    def _format_discord_payload(self, record: logging.LogRecord) -> dict:
        """Format log record as Discord embed."""
        return {
            "username": "First Alert System",
            "embeds": [
                {
                    "title": "CRITICAL ERROR",
                    "description": f"```{record.getMessage()[:2000]}```",
                    "color": 0xFF0000,
                    "fields": [
                        {
                            "name": "Logger",
                            "value": record.name,
                            "inline": True
                        },
                        {
                            "name": "Location",
                            "value": f"{record.filename}:{record.lineno}",
                            "inline": True
                        },
                        {
                            "name": "Function",
                            "value": record.funcName,
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
    
    async def _send_to_discord(self, payload: dict) -> None:
        """Send the payload to Discord webhook."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.webhook_url, json=payload, timeout=10)
        except Exception:
            pass


def setup_logging(name: str = "first") -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: Logger name (usually module name).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    if settings.ALERT_WEBHOOK:
        discord_handler = DiscordAlertHandler(settings.ALERT_WEBHOOK)
        logger.addHandler(discord_handler)
    
    return logger


def get_scraper_logger() -> logging.Logger:
    """Get logger for scraping module."""
    return setup_logging("first.scraper")


def get_consumer_logger() -> logging.Logger:
    """Get logger for queue consumer."""
    return setup_logging("first.consumer")


def get_notifications_logger() -> logging.Logger:
    """Get logger for notifications."""
    return setup_logging("first.notifications")
