"""Job queue consumer for processing notifications."""

import asyncio
import json
from typing import Dict

from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
import models
from clients import get_redis_client
from core.notifications.discord import discord_format, notify_discord
from core.notifications.telegram import telegram_format, notify_telegram
from logging_config import get_consumer_logger


logger = get_consumer_logger()


async def start_consuming() -> None:
    """
    starting the main queue consumer loop
    """
    redis_client = await get_redis_client()
    logger.info("Consumer started - listening for jobs...")

    while True:
        job_raw = None
        try:
            # move job from main queue to processing queue
            job_raw = await redis_client.blmove(
                settings.QUEUE_MAIN, 
                settings.QUEUE_PROCESSING, 
                30,
                "RIGHT", 
                "LEFT"
            )
            
            if job_raw is None:
                continue

            job = json.loads(job_raw)
            category = job[0]
            data = job[1]
            
            logger.info(f"Processing job: {data.get('project_id', 'unknown')} in {category}")
            
            await notifier(category, data)
            
            # Only remove from processing queue AFTER successful processing
            await redis_client.lrem(settings.QUEUE_PROCESSING, 1, job_raw)
            logger.info(f"Job {data.get('project_id', 'unknown')} completed")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode job JSON: {e}")
            # Remove malformed job from processing queue
            if job_raw:
                await redis_client.lrem(settings.QUEUE_PROCESSING, 1, job_raw)
                
        except Exception as e:
            # CRITICAL: Consumer crash - notify via Discord
            logger.critical(f"Consumer crashed: {e}")
            # Don't remove from processing queue - job can be retried
            await asyncio.sleep(5) 


async def notifier(category: str, data: Dict[str, str]) -> None:
    """
    Dispatch notifications to all active subscribers for a category.
    """
    async with AsyncSessionLocal() as db:
        # Get all active subscriptions for this category
        # Priority: Users with higher max_categories get notified first (premium prioritization)
        result = await db.execute(
            select(models.Subscription)
            .join(models.User, models.Subscription.user_id == models.User.id)
            .filter(
                models.Subscription.category == category,
                models.Subscription.is_active.is_(True)
            )
            .order_by(models.User.max_categories.desc())
        )
        subscriptions = result.scalars().all()
        
        logger.info(f"Notifying {len(subscriptions)} subscribers for {category}")

        # Send notifications to each subscriber
        for subscription in subscriptions:
            if subscription.platform == "telegram":
                formatted_data = await telegram_format(category, data)
                asyncio.create_task(notify_telegram(subscription.target_address, formatted_data))
            elif subscription.platform == "discord":
                formatted_data = await discord_format(category, data)
                asyncio.create_task(notify_discord(subscription.target_address, formatted_data))

        # Save job to database
        try:
            job = models.Job(
                external_id=data["project_id"],
                external_url=data["project_link"],
                category=category,
                title=data["project_title"],
                details=data["project_details"],
                budget=data["project_budget"],
                duration=data["project_duration"],
                owner_name=data["project_owner_name"],
                owner_registration_date=data["project_owner_registration_date"],
                owner_employment_rate=data["project_owner_employment_rate"],
                number_of_bids=data["project_number_of_bids"],
                published_at=data["project_date_published"]
            )
            db.add(job)
            await db.commit()
            logger.debug(f"Saved job {data['project_id']} to database")
        except Exception as e:
            logger.critical(f"Database error saving job {data.get('project_id')}: {e}")
            raise  # Re-raise to trigger retry logic
