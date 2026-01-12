"""Job queue publishing functionality."""

import json
from typing import Dict, List

from config import settings
from clients import get_redis_client


async def publish_jobs(payload: Dict[str, List[Dict[str, str]]]) -> None:
    """
    Publish processed jobs to the Redis queue.
    
    Args:
        payload: Dictionary mapping categories to lists of job data.
    """
    redis_client = await get_redis_client()
    
    for category, projects in payload.items():
        for job in projects:
            try:
                job_data = json.dumps([category, job])
                await redis_client.lpush(settings.QUEUE_MAIN, job_data)
            except Exception as e:
                print(f"Error publishing job {job.get('project_id', 'unknown')}: {e}")
                # Remove from seen set so it can be retried
                project_id = job.get("project_id")
                if project_id:
                    await redis_client.srem(f"ids:{category}", project_id)
