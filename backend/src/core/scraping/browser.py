"""Browser utilities for web scraping with Playwright."""

import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


async def init_browser(headless: bool = True) -> tuple[Playwright, Browser]:
    """
    Initialize a Playwright browser instance.
    
    Args:
        headless: Whether to run browser in headless mode.
        
    Returns:
        Tuple of (Playwright instance, Browser instance).
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    return playwright, browser


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
    )
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
