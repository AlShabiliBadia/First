from core.scraping import (
    init_browser,
    init_context,
    route_intercept,
    scrape_newest_jobs,
    scrape_data,
    Selectors,
)

from core.processing import (
    compare_and_process,
    normalize_data,
)

from core.notifications import (
    discord_format,
    notify_discord,
    telegram_format,
    notify_telegram,
)

from core.queue import start_consuming, notifier, publish_jobs

from clients import get_redis_client

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
