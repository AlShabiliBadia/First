"""Browser utilities for web scraping with Playwright."""

import asyncio
import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from logging_config import get_scraper_logger

logger = get_scraper_logger()

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
    "--memory-pressure-off",
    "--js-flags=--max-old-space-size=512",
]


async def init_browser(headless: bool = True, max_retries: int = 3) -> tuple[Playwright, Browser]:
    """
    Initialize a Playwright browser instance.
    
    Args:
        headless: Whether to run browser in headless mode.
        
    Returns:
        Tuple of (Playwright instance, Browser instance).
    """
    playwright = await async_playwright().start()
    
    last_error = None
    for attempt in range(max_retries):
        try:
            browser = await playwright.chromium.launch(
                headless=headless,
                args=BROWSER_ARGS,
            )
            return playwright, browser
        except Exception as e:
            last_error = e
            logger.warning(f"Browser launch attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    await playwright.stop()
    raise RuntimeError(f"Failed to launch browser after {max_retries} attempts: {last_error}")


async def init_context(browser: Browser) -> BrowserContext:
    """
    Create a new browser context with a random user agent.
    
    Args:
        browser: The browser instance to create context from.
        
    Returns:
        A new BrowserContext instance.
    """
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    # Set default navigation timeout for all pages in this context
    context.set_default_navigation_timeout(30000)
    context.set_default_timeout(15000)
    return context


async def route_intercept(route) -> None:
    """
    Intercept and abort requests for non-essential resources.
    
    Blocks: images, media, fonts, stylesheets to improve scraping speed.
    
    Args:
        route: The Playwright route object.
    """
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        await route.abort()
    else:
        await route.continue_()
