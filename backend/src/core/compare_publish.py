import json
from utils import get_redis_client
from config import settings
from scrape import scrape_data

def compare_jobs(newest_jobs: dict[str, dict[str, str]]):
    r = get_redis_client()

    new_jobs: dict[str, list[tuple[str, str]]] = {}

    for category, jobs in newest_jobs.items():
        for job_id, job_link in jobs.items():
            if r.sismember(category, job_id):
                continue
            new_jobs[category] = [(job_id, job_link)]

    scrape_data(new_jobs)


def publish_jobs(payload: dict[str, list[dict[str, str]] | str]):
    r = get_redis_client()
    r.lpush(settings.QUEUE_MAIN, json.dumps(payload))


