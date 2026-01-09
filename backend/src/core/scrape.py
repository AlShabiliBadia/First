from compare_publish import compare_jobs, publish_jobs
from utils import init_browser, init_context, get_redis_client
from config import settings




# to intercept requests and abort these resources "saves time"
def route_intercept(route):
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def scrape_newest_jobs():
    p, browser = init_browser()
    context = init_context(browser)

    context.route("**/*", route_intercept)


    page = context.new_page()
    
    newest_jobs = {i: {} for i in settings.CATEGORIES}
    for i in settings.CATEGORIES:
        try:
            #CATEGORIES = [business, development, engineering-architecture, design, marketing, writing-translation, support, training]
            page.goto(f"https://mostaql.com/projects?category={i}&sort=latest&page=1")
            rows = page.locator("tr.project-row").all()


            # each page has multiple jobs, we will just scrape the link of each job
            for row in rows[:10]:
                title_link = row.locator("h2 a").first
                url = title_link.get_attribute("href")
                project_id = url.split("/project/")[1].split("-")[0]

                newest_jobs[i][project_id] = url
                
        except Exception as e:
            print(f"Failed to scrape newest jobs due to error: {e}")


    browser.close()
    p.stop()
    
    compare_jobs(newest_jobs)

def scrape_data(jobs: dict[str, list[tuple[str, str]]]):
    p, browser = init_browser()
    
    r = get_redis_client()
    
    for category, link_items in jobs.items():
        context = init_context(browser)
        context.route("**/*", route_intercept)
        page = context.new_page()
        
        payload: dict[str, list[dict[str, str]] | str] = {
            "category": category,
            "data": []
            }
        
        for project_id, link in link_items:
            try:
                page.goto(link, timeout=20000, wait_until="domcontentloaded")
                page.wait_for_selector(".page-title h1", timeout=5000)


                project_title = page.locator(".page-title").locator("h1").get_attribute("data-page-title") # title of the project
                
                description_locator = page.locator("#projectDetailsTab .text-wrapper-div")
                if description_locator.count() > 0:
                    project_details = "\n".join(description_locator.all_inner_texts()) # description of the project
                else: project_details = ""

                project_panel = page.locator("#project-meta-panel-panel")
                
                try: date_published = project_panel.locator(".meta-row").filter(has_text="تاريخ النشر").locator(".meta-value time").get_attribute("data-original-title") # date published of the project
                except: date_published = "N/A"

                try: budget = project_panel.locator('[data-type="project-budget_range"]').inner_text() # budget of the project
                except: budget = "N/A"
                
                try: duration = project_panel.locator(".meta-row").filter(has_text="مدة التنفيذ").locator(".meta-value").inner_text() # duration of the project
                except: duration = "N/A"
                    
                project_panel_user = project_panel.locator(".profile-details")
                project_owner_name = project_panel_user.locator("h5").inner_text() # name of the project owner
                number_of_bids = page.locator('.bid').count() # number of bids

                try:
                    project_owner_registration_date = project_panel_user.locator(".table tr").nth(0).locator("td").nth(1).inner_text() # registration date of the project owner
                    project_owner_employment_rate = project_panel_user.locator(".table tr").nth(1).locator("td").nth(1).inner_text() # employment rate of the project owner
                except:
                    project_owner_registration_date = "N/A"
                    project_owner_employment_rate = "N/A"

                
                payload[category].append({
                    "project_id": project_id,
                    "project_title": project_title,
                    "project_details": project_details,
                    "project_date_published": date_published,
                    "project_budget": budget,
                    "project_duration": duration,
                    "project_owner_name": project_owner_name,
                    "project_owner_registration_date": project_owner_registration_date,
                    "project_owner_employment_rate": project_owner_employment_rate,
                    "project_number_of_bids": number_of_bids
                })


        publish_jobs(payload)
                

            except Exception as e:
                print(f"Error {project_id}: {e}")
                continue

        if context:
            context.close()
            print(f"Closed Context for {category}")
        
        time.sleep(2)

    browser.close()
    p.stop()



    