"""
Core module for job scraping and notification system.

Submodules:
    - scraping: Browser utilities and job scraping logic
    - processing: Data normalization, comparison, and publishing
    - notifications: Discord and Telegram notification services
    - queue: Job queue consumer
    - clients: External service clients (Redis)
"""

# Scraping
from core.scraping import (
    init_browser,
    init_context,
    route_intercept,
    scrape_newest_jobs,
    scrape_data,
    Selectors,
)

# Processing
from core.processing import (
    compare_and_process,
    normalize_data,
)

# Notifications
from core.notifications import (
    discord_format,
    notify_discord,
    telegram_format,
    notify_telegram,
)

# Queue
from core.queue import start_consuming, notifier, publish_jobs

# Clients
from core.clients import get_redis_client

__all__ = [
    # Scraping
    "init_browser",
    "init_context",
    "route_intercept",
    "scrape_newest_jobs",
    "scrape_data",
    "Selectors",
    # Processing
    "compare_and_process",
    "normalize_data",
    "publish_jobs",
    # Notifications
    "discord_format",
    "notify_discord",
    "telegram_format",
    "notify_telegram",
    # Queue
    "start_consuming",
    "notifier",
    # Clients
    "get_redis_client",
]
