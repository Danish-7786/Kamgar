
import pika 
import time
import threading
from scraper.linkedin_bot import run_scraper
from scraper.job_scrapper import job_scrapper
from Queue.job_queue import ai_worker, process_job, process_linkedin_job

def clean_val(val):
    if val is None or (isinstance(val, float) and str(val).lower() == 'nan'):
        return ""
    return str(val).strip()

if __name__ == "__main__":
    print("Initializing Distributed Job Matching Pipeline...")
    
    # 1. Start the AI Consumer (worker) in a background thread
    worker_thread = threading.Thread(target=ai_worker, daemon=True)

    worker_thread.start()
    print("Background AI Worker started. Listening for jobs in RabbitMQ...")
    
    try:
        # 2. Start the Scraper (Producer) on the main thread
        print("Starting LinkedIn Job Scraper...")
        # run_scraper(on_job_found_callback=process_linkedin_job)
        jobs_df = job_scrapper(site_name=["indeed","linkedin","naukri","bayt","glassdoor","google"])
        print("Scrapper finished its work")
        
        print("Data type:", type(jobs_df))
        # Get a quick summary of columns, count of non-null values, and their data types
        print("\n--- DataFrame Info ---")
        jobs_df.info()
        
        # Iterate over each scraped job and push to RabbitMQ
        print("\nProcessing broad scraper results...")
        for index, row in jobs_df.iterrows():
            title = clean_val(row.get('title'))
            # print("title",title)
            company = clean_val(row.get('company'))
            # print("company",company)

            # Note: Broad scraper uses 'job_url' or 'job_url_direct' instead of 'link'
            link = clean_val(row.get('job_url') or row.get('job_url_direct'))
            # print("link",link)

            description = clean_val(row.get('description'))
            # print("description",description)
            
            # Run deterministic filter and queue job if it matches
            process_job(title=title, company=company, link=link, description=description)
            
        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        while True:
            queue = channel.queue_declare(queue='jobs_queue', passive=True)
            count = queue.method.message_count
            if count == 0:
                print("No pending jobs in queue.")
                run_scraper(on_job_found_callback=process_linkedin_job)
                break

            print(f"{count} jobs remaining in the queue...")
            time.sleep(10)
            
        connection.close()
            
    except Exception as e:
        print(f"Pipeline crashed: {e}")
