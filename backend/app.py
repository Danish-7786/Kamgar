
from scraper.job_scrapper import job_scrapper
from contextlib import asynccontextmanager
from db.models import DatabaseManager
import os
from datetime import datetime
import threading 
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from Queue.job_queue import process_job,ai_worker
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
# Platforms supported by the underlying jobspy scraper.
ALLOWED_PLATFORMS = ["indeed", "linkedin", "google", "glassdoor", "zip_recruiter", "bayt", "naukri", "bdjobs"]
DEFAULT_PLATFORMS = ["indeed", "linkedin", "google"]


class ScrapeRequest(BaseModel):
    platforms: list[str] = DEFAULT_PLATFORMS


db = DatabaseManager()


scraper_status = {
    "is_running": False,
    "last_run": None,
    "jobs_processed":0,
    "offset": 0
}

import json

STATUS_FILE = "scraper_status.json"

def load_status():
    global scraper_status
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                saved = json.load(f)
                # Ensure is_running is False on startup to prevent stuck states
                saved["is_running"] = False
                scraper_status.update(saved)
        except Exception as e:
            print(f"Failed to load scraper status: {e}")

def save_status():
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(scraper_status, f, indent=4)
    except Exception as e:
        print(f"Failed to save scraper status: {e}")

# How many results per site to pull per run; also the amount the offset
# advances each run so consecutive scrapes page through fresh jobs.
BATCH_SIZE = 80

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database tables...")
    db.create_table()
    print("Loading scraper status...")
    load_status()
    print("Starting background AI consumer worker thread ....")
    worker_thread = threading.Thread(target= ai_worker, daemon=True)
    worker_thread.start()
    yield
    print("Closing Database connection...")
    db.close()

app = FastAPI(
    title = "Job Scrapper & Matcher API",
    description="API to query matched jobs and trigger the scraping pipeline.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_scrapper_task(site_name=None):
    global scraper_status
    # global is used to read global variable
    if not site_name:
        site_name = DEFAULT_PLATFORMS
    scraper_status["jobs_processed"] = 0
    scraper_status["is_running"] = True
    save_status()
    try:
        offset = scraper_status.get("offset", 0)
        jobs_df = job_scrapper(site_name=site_name, results_wanted=BATCH_SIZE, offset=offset)
        # Advance the offset so the next run pages into fresh results.
        # If this batch came back empty we've exhausted the listings, so
        # wrap back to the start instead of paging into nothing forever.
        scraper_status["offset"] = 0 if len(jobs_df) == 0 else offset + BATCH_SIZE
        save_status()
        def clean_val(val):
            if val is None or (isinstance(val, float)) and str(val).lower() == 'nan':
                return ""
            return str(val).strip()
        count=0
       
        for index,row in jobs_df.iterrows():
            title = clean_val(row.get("title"))
            company = clean_val(row.get("company"))
            
            # Safely parse date_posted to YYYY-MM-DD format
            raw_date = row.get("date_posted")
            date_posted = ""
            if pd.notna(raw_date):
                try:
                    date_posted = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
                except Exception:
                    date_posted = clean_val(raw_date)

            link = clean_val(row.get("job_url") or row.get("job_url_direct"))
            description = clean_val(row.get("description"))
    
            # Pre-filter and publish to RabbitMQ
            process_job(title=title, company=company, date_posted=date_posted, link=link, description=description)
            count +=1
        scraper_status["jobs_processed"] = count
        scraper_status["last_run"] = datetime.now().isoformat()
        save_status()
    except Exception as e:
        print(f"Error during background scraper task: {e}")
    finally:
        scraper_status["is_running"] = False
        save_status()



@app.get("/jobs",summary = "Fetch evaluated jobs from database")
def get_jobs(
    min_score : int = Query(0, description = "Minimum AI matching score filter",ge=0,le=100),
    verdict : str = Query(None, description = "AI verdict filter (e.g., 'Strong Match','Partial Match')"),
    page_size: int = Query(10, description="Number of records to fetch", ge=1, le=100),
    page: int = Query(1, description="1-based page number", ge=1),
    sort_by: str = Query("created_at", description="Sort criteria ('created_at' or 'score')"),
    ):
    offset = (page - 1) * page_size
    limit = page_size
    result = db.fetch_jobs(min_score= min_score, verdict=verdict,limit=limit,offset=offset, sort_by=sort_by)
    return {
        "status":"success",
        "total_count":result["total_count"],
        "pages":result["pages"],
        "page":page,
        "page_size":page_size,
        
        "data":result["jobs"]
        }

@app.get("/job/{job_id}", summary = "Fetch the job by job_id")
def get_job_by_id(job_id: int):
    job = db.fetch_jobs_by_id(job_id)
    if not job:
        return HTTPException(status_code = 404, detail="Job not found")
    return {"status":"success", "data":job}

@app.post("/scrape",summary = "Triger the job scrapper background task")
def trigger_scrape(background_tasks: BackgroundTasks, body: ScrapeRequest = ScrapeRequest()):
    if scraper_status["is_running"]:
        return {"status":"ignored","message":"Scraper is already running"}
    platforms = [p for p in body.platforms if p in ALLOWED_PLATFORMS]
    if not platforms:
        raise HTTPException(status_code=400, detail="No valid platforms selected")
    background_tasks.add_task(run_scrapper_task, platforms)
    return {
        "status":"success",
        "message":f"Scraper triggered for: {', '.join(platforms)}",
        "platforms": platforms,
    }

@app.get("/status",summary= "Check the API status ")
def get_status():
    db_healthy = False
    try:
        if db.connection and not db.connection.closed:
            db_healthy = True
    except Exception:
        pass
    return {
        "scraper": scraper_status,
        "database":"connected" if db_healthy else "disconnected"
    } 

  