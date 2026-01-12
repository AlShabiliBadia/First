"""Job comparison and deduplication logic."""

from typing import Dict, List, Tuple

from clients import get_redis_client


async def compare_and_process(newest_jobs: Dict[str, Dict[str, str]]) -> None:
    """
    Compare incoming jobs against known jobs and process new ones.
    
    Args:
        newest_jobs: Dictionary mapping category names to dictionaries of {job_id: job_url}.
    """
    redis_client = await get_redis_client()

    # category -> [(job_id, job_link), ...]
    jobs_to_scrape: Dict[str, List[Tuple[str, str]]] = {}

    for category, jobs_dict in newest_jobs.items():
        incoming_ids = list(jobs_dict.keys())
        if not incoming_ids:
            continue

        # Check which job IDs we've already seen
        are_members = await redis_client.smismember(f"ids:{category}", incoming_ids)

        new_ids = []
        for job_id, is_seen in zip(incoming_ids, are_members):
            if not is_seen:
                new_ids.append(job_id)
                
                # Add to local processing list
                if category not in jobs_to_scrape:
                    jobs_to_scrape[category] = []
                jobs_to_scrape[category].append((job_id, jobs_dict[job_id]))

        # Mark new IDs as seen in Redis
        if new_ids:
            await redis_client.sadd(f"ids:{category}", *new_ids)

    # Scrape the new jobs if any found
    if jobs_to_scrape:
        # Import here to avoid circular dependency
        from core.scraping.job_scraper import scrape_data
        await scrape_data(jobs_to_scrape)
