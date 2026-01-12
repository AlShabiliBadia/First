from typing import Dict

import httpx

from config import settings
from logging_config import get_notifications_logger


logger = get_notifications_logger()

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


async def telegram_format(category: str, data: Dict[str, str]) -> str:
    """
    Format job data as a Telegram message.
    """
    message = f"""
 *New Job Alert*

 *{data.get('project_title', 'Unknown Title')}*
 [View Project]({data.get('project_link', '')})

━━ Project Overview ━━
 Category: {category}
 Budget: {data.get('project_budget', 'N/A')}
 Duration: {data.get('project_duration', 'N/A')}
 Bids: {data.get('project_number_of_bids', '0')}

━━ Client Information ━━
 Owner: {data.get('project_owner_name', 'N/A')}
 Employment Rate: {data.get('project_owner_employment_rate', 'N/A')}
 Member Since: {data.get('project_owner_registration_date', 'N/A')}

_Powered by First_
"""
    return message.strip()


async def notify_telegram(chat_id: str, message: str) -> bool:
    """
    Send a notification to a Telegram chat.
    
    Args:
        chat_id: The Telegram chat ID.
        message: The formatted message to send.
        
    Returns:
        True if successful, False otherwise.
    """
    if not settings.TELEGRAM_TOKEN:
        logger.warning("Telegram token not configured")
        return False
    
    url = TELEGRAM_API_URL.format(token=settings.TELEGRAM_TOKEN)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Telegram notification sent to {chat_id}")
                return True
            
            logger.warning(f"Telegram API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.warning(f"Telegram notification error: {e}")
        return False
