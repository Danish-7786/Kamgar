
from scraper.job_scrapper import job_scrapper
from contextlib import asynccontextmanager
from db.models import DatabaseManager
import os
from datetime import datetime
import threading 
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from Queue.job_queue import process_job,ai_worker
from fastapi.middleware.cors import CORSMiddleware


db = DatabaseManager()


scraper_status = {
    "is_running": False,
    "last_run": None,
    "jobs_processed":0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database tables...")
    db.create_table()
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


def run_scrapper_task():
    global scraper_status
    # global is used to read global variable
    scraper_status["jobs_processed"] = 0
    scraper_status["is_running"] = True
    try: 
        jobs_df = job_scrapper(site_name=["indeed","linkedin","naukri","bayt","glassdoor","google"])
        def clean_val(val):
            if val is None or (isinstance(val, float)) and str(val).lower() == 'nan':
                return ""
            return str(val).strip()
        count=0
        for index,row in jobs_df.iterrows():
            title = clean_val(row.get("title"))
            company = clean_val(row.get("company"))
            link = clean_val(row.get("job_url") or row.get("job_url_direct"))
            description = clean_val(row.get("description"))
    

             # Pre-filter and publish to RabbitMQ
            process_job(title=title, company=company, link=link, description=description)
            count +=1
        scraper_status["jobs_processed"] = count
        scraper_status["last_run"] = datetime.now().isoformat()
    except Exception as e:
        print(f"Error during background scraper task: {e}")
    finally:
        scraper_status["is_running"] = False



@app.get("/jobs",summary = "Fetch evaluated jobs from database")
def get_jobs(
    min_score : int = Query(0, description = "Minimum AI matching score filter",ge=0,le=100),
    verdict : str = Query(None, description = "AI verdict filter (e.g., 'Strong Match','Partial Match')")):
    jobs = db.fetch_jobs(min_score= min_score, verdict=verdict)
    return {"status":"success","count":len(jobs), "data":jobs}

@app.get("/job/{job_id}", summary = "Fetch the job by job_id")
def get_job_by_id(job_id: int):
    job = db.fetch_jobs_by_id(job_id)
    if not job:
        return HTTPException(status_code = 404, detail="Job not found")
    return {"status":"success", "data":job}

@app.post("/scrape",summary = "Triger the job scrapper background task")
def trigger_scrape(background_tasks: BackgroundTasks):
    if scraper_status["is_running"]:
        return {"status":"ignored","message":"Scraper is already running"}
    background_tasks.add_task(run_scrapper_task)
    return {"status":"success", "message":"Scrapper triggered in the background"}

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

  