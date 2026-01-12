"""Discord notification functionality."""

from datetime import datetime, timezone
from typing import Dict

import httpx

from logging_config import get_notifications_logger


logger = get_notifications_logger()


async def discord_format(category: str, data: Dict[str, str]) -> dict:
    """
    Format job data as a Discord webhook message.
    """
    return {
        "username": "First",
        "avatar_url": "https://alshabili.site/logo.png",

        "embeds": [
            {
                "title": data.get("project_title", "Unknown Title"),
                "url": data.get("project_link", ""),
                "color": 0x800080,

                "fields": [
                    {
                        "name": "━━━━━━━━━━ Project Overview ━━━━━━━━━━",
                        "value": "\u200b",
                        "inline": False
                    },
                    {
                        "name": "Category",
                        "value": category,
                        "inline": False
                    },
                    {
                        "name": "Budget",
                        "value": data.get("project_budget", "N/A"),
                        "inline": False
                    },
                    {
                        "name": "Duration",
                        "value": data.get("project_duration", "N/A"),
                        "inline": False
                    },
                    {
                        "name": "Bids",
                        "value": str(data.get("project_number_of_bids", "0")),
                        "inline": False
                    }
                ],

            },
            {
                "color": 0x800080,

                "fields": [
                    {
                        "name": "━━━━━━━━━━ Client Information ━━━━━━━━━━",
                        "value": "\u200b",
                        "inline": False
                    },
                    {
                        "name": "Owner Name",
                        "value": data.get("project_owner_name", "N/A"),
                        "inline": False
                    },
                    {
                        "name": "Owner Employment Rate",
                        "value": data.get("project_owner_employment_rate", "N/A"),
                        "inline": False
                    },
                    {
                        "name": "Member Since",
                        "value": data.get("project_owner_registration_date", "N/A"),
                        "inline": False
                    },
                ],
                "footer": {
                    "text": "Powered by First",
                    "icon_url": "https://alshabili.site/logo.png"
                },

                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }


async def notify_discord(webhook_url: str, data: dict) -> bool:
    """
    Send a notification to a Discord webhook.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data, timeout=10)
            
            if response.status_code in (200, 204):
                logger.debug(f"Discord notification sent successfully")
                return True
            
            logger.warning(f"Discord webhook failed: status {response.status_code}")
            return False
            
    except Exception as e:
        logger.warning(f"Discord notification error: {e}")
        return False
