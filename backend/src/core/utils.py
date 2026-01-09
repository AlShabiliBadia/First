import random
from playwright.sync_api import sync_playwright
import redis

from config import settings

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def init_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    return p, browser

def init_context(browser):
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
    )
    return context


def get_redis_client():
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASS,
            decode_responses=True,
            socket_timeout=5
        )
        
        client.ping()
        return client
        
    except redis.AuthenticationError:
        print("Authentication failed. Check your password.")
    except redis.ConnectionError:
        print("Redis is unreachable. Is Docker running?")

