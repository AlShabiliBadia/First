"""Job scraping functionality for Mostaql.com."""

from typing import Dict, List, Tuple

from config import settings
from core.scraping.browser import init_browser, init_context, route_intercept
from core.scraping.selectors import Selectors
from clients import get_redis_client
from core.processing.comparator import compare_and_process
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
        context = await init_context(browser)
        try:
            await context.route("**/*", route_intercept)
            page = await context.new_page()
            
            newest_jobs: Dict[str, Dict[str, str]] = {category: {} for category in settings.CATEGORIES}
            
            for category in settings.CATEGORIES:
                try:
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
        
        await compare_and_process(newest_jobs)
        
    finally:
        await browser.close()
        await playwright.stop()


async def scrape_data(jobs: Dict[str, List[Tuple[str, str]]]) -> None:
    """
    Scrape detailed data for specific jobs.
    
    Args:
        jobs: Dictionary mapping category names to lists of (project_id, url) tuples.
    """
    total_jobs = sum(len(v) for v in jobs.values())
    logger.info(f"Scraping details for {total_jobs} new jobs...")
    
    playwright, browser = await init_browser()
    redis_client = await get_redis_client()
    
    payload: Dict[str, List[dict]] = {}

    try:
        for category, link_items in jobs.items():
            context = await init_context(browser)
            try:
                await context.route("**/*", route_intercept)
                page = await context.new_page()
                
                payload[category] = []
                
                for project_id, link in link_items:
                    try:
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
        payload = await normalize_data(payload)
        await publish_jobs(payload)
        logger.info(f"Published {total_jobs} jobs to queue")

    finally:
        await browser.close()
        await playwright.stop()


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
