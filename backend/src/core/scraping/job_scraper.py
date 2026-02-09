"""Job scraping functionality for Mostaql.com."""

from typing import Dict, List, Optional, Tuple

from playwright.async_api import Browser, Playwright

from config import settings
from core.scraping.browser import init_browser, init_context, route_intercept
from core.scraping.selectors import Selectors
from clients import get_redis_client
from core.processing.normalizer import normalize_data
from core.queue.publisher import publish_jobs
from logging_config import get_scraper_logger


logger = get_scraper_logger()


async def scrape_newest_jobs() -> None:
    """
    Scrape the newest job listings from all categories.
    
    Fetches the first 10 jobs from each category's listing page,
    then compares them against known jobs to find new ones.
    """
    playwright, browser = await init_browser()
    
    try:
        if not browser.is_connected():
            raise RuntimeError("Browser disconnected before context creation")
            
        context = await init_context(browser)
        try:
            await context.route("**/*", route_intercept)
            page = await context.new_page()
            
            newest_jobs: Dict[str, Dict[str, str]] = {category: {} for category in settings.CATEGORIES}
            
            for category in settings.CATEGORIES:
                try:
                    # Check browser health before each category
                    if not browser.is_connected():
                        raise RuntimeError("Browser disconnected during scraping")
                    
                    await page.goto(
                        Selectors.get_category_url(category),
                        timeout=20000,
                        wait_until="domcontentloaded"
                    )
                    rows = await page.locator(Selectors.PROJECT_ROW).all()

                    # Scrape up to 10 jobs per category
                    for row in rows[:10]:
                        title_link = row.locator(Selectors.PROJECT_TITLE_LINK).first
                        url = await title_link.get_attribute("href")
                        project_id = url.split("/project/")[1].split("-")[0]
                        newest_jobs[category][project_id] = url
                    
                    logger.info(f"Scraped {len(newest_jobs[category])} jobs from {category}")
                        
                except Exception as e:
                    logger.error(f"Failed to scrape category '{category}': {e}")
        finally:
            await context.close()
        
        # Compare and process new jobs - reusing the same browser instance
        await _compare_and_scrape_details(newest_jobs, playwright, browser)
        
    finally:
        await browser.close()
        await playwright.stop()


async def _compare_and_scrape_details(
    newest_jobs: Dict[str, Dict[str, str]], 
    playwright: Playwright,
    browser: Browser
) -> None:
    """
    Compare incoming jobs against known jobs and scrape details for new ones.
    Reuses the existing browser instance to avoid resource conflicts.
    
    Args:
        newest_jobs: Dictionary mapping category names to dictionaries of {job_id: job_url}.
        playwright: The Playwright instance to reuse.
        browser: The Browser instance to reuse.
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

    # Scrape the new jobs if any found - reusing the browser
    if jobs_to_scrape:
        await _scrape_job_details(jobs_to_scrape, browser, redis_client)


async def _scrape_job_details(
    jobs: Dict[str, List[Tuple[str, str]]], 
    browser: Browser,
    redis_client
) -> None:
    """
    Scrape detailed data for specific jobs using an existing browser instance.
    
    Args:
        jobs: Dictionary mapping category names to lists of (project_id, url) tuples.
        browser: The Browser instance to reuse.
        redis_client: Redis client for cleanup on failures.
    """
    total_jobs = sum(len(v) for v in jobs.values())
    logger.info(f"Scraping details for {total_jobs} new jobs...")
    
    payload: Dict[str, List[dict]] = {}

    for category, link_items in jobs.items():
        # Check browser health before each category
        if not browser.is_connected():
            logger.error("Browser disconnected during detail scraping")
            break
            
        context = await init_context(browser)
        try:
            await context.route("**/*", route_intercept)
            page = await context.new_page()
            
            payload[category] = []
            
            for project_id, link in link_items:
                try:
                    # Check browser health before each job
                    if not browser.is_connected():
                        raise RuntimeError("Browser disconnected during job scraping")
                    
                    await page.goto(link, timeout=20000, wait_until="domcontentloaded")
                    await page.wait_for_selector(Selectors.PAGE_TITLE, timeout=5000)

                    # Extract project data
                    project_data = await _extract_project_data(page, project_id, link)
                    payload[category].append(project_data)
                    logger.debug(f"Scraped details for {project_id}")

                except Exception as e:
                    logger.warning(f"Failed to scrape project {project_id}: {e}")
                    await redis_client.srem(f"ids:{category}", project_id)
        finally:
            await context.close()

    # Normalize and publish the data
    if payload:
        payload = await normalize_data(payload)
        await publish_jobs(payload)
        logger.info(f"Published {total_jobs} jobs to queue")


async def _extract_project_data(page, project_id: str, link: str) -> dict:
    """
    Extract all data from a project detail page.
    
    Args:
        page: The Playwright page object.
        project_id: The project's unique ID.
        link: The project's URL.
        
    Returns:
        Dictionary containing all project data.
    """
    # Project title
    project_title = await page.locator(".page-title").locator("h1").get_attribute("data-page-title")
    
    # Project details/description
    description_locator = page.locator(Selectors.PROJECT_DETAILS_TAB)
    description_count = await description_locator.count()
    if description_count > 0:
        project_details = "\n".join(await description_locator.all_inner_texts())
    else:
        project_details = ""

    # Meta panel data
    project_panel = page.locator(Selectors.PROJECT_META_PANEL)
    
    # Date published
    try:
        date_published = await project_panel.locator(Selectors.DATE_PUBLISHED_ROW).filter(
            has_text=Selectors.DATE_PUBLISHED_TEXT
        ).locator(Selectors.META_VALUE_TIME).get_attribute("data-original-title")
    except Exception:
        date_published = "N/A"

    # Budget
    try:
        budget = await project_panel.locator(Selectors.BUDGET_SELECTOR).inner_text()
    except Exception:
        budget = "N/A"
    
    # Duration
    try:
        duration = await project_panel.locator(Selectors.DATE_PUBLISHED_ROW).filter(
            has_text=Selectors.DURATION_TEXT
        ).locator(Selectors.META_VALUE).inner_text()
    except Exception:
        duration = "N/A"
        
    # Owner information
    project_panel_user = project_panel.locator(Selectors.PROFILE_DETAILS)
    project_owner_name = await project_panel_user.locator(Selectors.OWNER_NAME).inner_text()
    
    try:
        project_owner_registration_date = await project_panel_user.locator(
            Selectors.OWNER_TABLE
        ).nth(0).locator("td").nth(1).inner_text()
        project_owner_employment_rate = await project_panel_user.locator(
            Selectors.OWNER_TABLE
        ).nth(1).locator("td").nth(1).inner_text()
    except Exception:
        project_owner_registration_date = "N/A"
        project_owner_employment_rate = "N/A"

    # Number of bids
    number_of_bids = await page.locator(Selectors.BID).count()

    return {
        "project_id": project_id,
        "project_link": link,
        "project_title": project_title,
        "project_details": project_details,
        "project_date_published": date_published,
        "project_budget": budget,
        "project_duration": duration,
        "project_owner_name": project_owner_name,
        "project_owner_registration_date": project_owner_registration_date,
        "project_owner_employment_rate": project_owner_employment_rate,
        "project_number_of_bids": str(number_of_bids)
    }
