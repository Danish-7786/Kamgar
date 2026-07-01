import threading
from scraper.linkedin_bot import run_scraper
from Queue.job_queue import ai_worker, process_job

if __name__ == "__main__":
    print("Initializing Distributed Job Matching Pipeline...")
    
    # 1. Start the AI Consumer (worker) in a background thread
    worker_thread = threading.Thread(target=ai_worker, daemon=True)
    worker_thread.start()
    print("🤖 Background AI Worker started. Listening for jobs in RabbitMQ...")
    
    try:
        # 2. Start the Scraper (Producer) on the main thread
        print("🔍 Starting LinkedIn Job Scraper...")
        run_scraper(on_job_found_callback=process_job)
        
    except Exception as e:
        print(f"Pipeline crashed: {e}")