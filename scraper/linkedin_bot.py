import logging
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters

def run_scraper(on_job_found_callback):
    """
    Initializes and runs the LinkedIn Scraper.
    Fires the on_job_found_callback every time a job is extracted.
    """
    logging.basicConfig(level=logging.INFO)

    # 1. Initialize the scraper
    scraper = LinkedinScraper(
        chrome_executable_path=None, 
        chrome_options=None,  
        headless=True, 
        max_workers=1, 
        slow_mo=2.5, 
        page_load_timeout=40000
    )

    # 2. Bind the custom callback passed from main.py to the DATA event
    scraper.on(Events.DATA, on_job_found_callback)
    
    # Optional: Add error and invalid event listeners for better debugging
    scraper.on(Events.ERROR, lambda error: print(f"Scraper Error: {error}"))
    scraper.on(Events.INVALID_SESSION, lambda: print("Invalid session!"))

    # 3. Define your search parameters
    queries = [
        Query(
            query='Software Engineer',
            options=QueryOptions(
                locations=['India'],
                apply_link=True,
                limit=20,  # LIMIT TO 5 FOR TESTING so it doesn't run forever!
                filters=QueryFilters(
                    relevance=RelevanceFilters.RECENT,
                    time=TimeFilters.DAY,
                    type=[TypeFilters.FULL_TIME]
                )
            )
        )
    ]

    print("Starting LinkedIn Scraper...")
    scraper.run(queries)
    print("Scraping finished.")