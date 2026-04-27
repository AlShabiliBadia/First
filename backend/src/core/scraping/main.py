"""Main entry point for the scraper service."""

import asyncio
import traceback

from core.scraping import scrape_newest_jobs
from core.scraping.browser import _kill_orphaned_browser_processes
from logging_config import get_scraper_logger
from config import settings

logger = get_scraper_logger()

SCRAPE_INTERVAL_SECONDS = settings.SCRAPE_INTERVAL_SECONDS
MAX_CONSECUTIVE_FAILURES = 10
BASE_BACKOFF_SECONDS = 30
MAX_BACKOFF_SECONDS = 300  # 5 minutes


async def run_scraper_loop() -> None:
    """
    Run the scraper in an infinite loop with resilient error handling.
    
    Features:
    - Consecutive failure tracking with exponential backoff
    - Orphan process cleanup after every crash
    - Extended cooldown after too many consecutive failures
    """
    logger.info(f"Starting scraper loop (interval: {SCRAPE_INTERVAL_SECONDS}s)")
    consecutive_failures = 0

    while True:
        try:
            logger.info("Scraping newest jobs...")
            await scrape_newest_jobs()
            logger.info("Scrape complete. Sleeping...")
            consecutive_failures = 0  # Reset on success
        except Exception as e:
            consecutive_failures += 1
            logger.critical(
                f"Scraper crashed ({consecutive_failures}x consecutive): {e}\n"
                f"{traceback.format_exc()}"
            )

            # Safety net: kill any orphaned child processes that leaked
            _kill_orphaned_browser_processes()

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.critical(
                    f"{MAX_CONSECUTIVE_FAILURES} consecutive failures — "
                    f"cooling down for {MAX_BACKOFF_SECONDS}s"
                )
                await asyncio.sleep(MAX_BACKOFF_SECONDS)
                consecutive_failures = 0
                continue

        # Exponential backoff on failures, normal interval on success
        if consecutive_failures > 0:
            sleep_time = min(
                BASE_BACKOFF_SECONDS * (2 ** (consecutive_failures - 1)),
                MAX_BACKOFF_SECONDS,
            )
            logger.info(f"Backing off for {sleep_time}s before retry...")
        else:
            sleep_time = SCRAPE_INTERVAL_SECONDS

        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(run_scraper_loop())
