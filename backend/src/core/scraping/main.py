"""Main entry point for the scraper service."""

import asyncio

from core.scraping import scrape_newest_jobs
from logging_config import get_scraper_logger


logger = get_scraper_logger()

SCRAPE_INTERVAL_SECONDS = 60


async def run_scraper_loop() -> None:
    """
    Run the scraper in an infinite loop.
    
    Scrapes newest jobs every SCRAPE_INTERVAL_SECONDS.
    """
    logger.info(f"Starting scraper loop (interval: {SCRAPE_INTERVAL_SECONDS}s)")
    
    while True:
        try:
            logger.info("Scraping newest jobs...")
            await scrape_newest_jobs()
            logger.info("Scrape complete. Sleeping...")
        except Exception as e:
            logger.critical(f"Scraper crashed: {e}")
        
        await asyncio.sleep(SCRAPE_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run_scraper_loop())
