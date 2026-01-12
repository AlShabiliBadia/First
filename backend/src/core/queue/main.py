"""Main entry point for the consumer service."""

import asyncio

from core.queue.consumer import start_consuming


if __name__ == "__main__":
    asyncio.run(start_consuming())
