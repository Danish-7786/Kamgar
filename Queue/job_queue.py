import pika
import json
import threading
import time
from scraper.linkedin_bot import run_scraper
from linkedin_jobs_scraper.events import EventData
from scorer.deterministic_job_scrorer import DeterministicJobScorer

from scorer.ai_scorer import AIScorer

ai_scorer = AIScorer();

# Initialize the deterministic filter globally
job_filter = DeterministicJobScorer()

# --- RABBITMQ CONNECTION SETUP ---
def get_rabbitmq_channel():
    # Assumes RabbitMQ is running locally via Docker
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    # durable=True ensures the queue survives a RabbitMQ restart
    channel.queue_declare(queue='jobs_queue', durable=True)
    return connection, channel

# --- 1. THE PRODUCER (Scraper) ---
def process_job(data: EventData):
    """
    PRODUCER: This callback pre-filters the job, and if it passes, publishes to RabbitMQ.
    """
    clean_desc = data.description.replace('\n', ' ').strip()
    
    # Run the fast, free regex filter first
    result = job_filter.score_job(title=data.title, description=clean_desc)
    
    if result["verdict"] == "REJECTED":
        print(f"❌ DROPPED ({data.title}): {result['reason']}")
        return # Exit early, don't send to queue!

    print(f"📥 Scraper found MATCH: {data.title} - Publishing to RabbitMQ...")
    
    # We need a new connection per thread in pika
    connection, channel = get_rabbitmq_channel()
    
    # Create a simple dictionary payload
    job_payload = {
        "title": data.title,
        "company": data.company,
        "link": data.link,
        "description": data.description.replace('\n', ' ').strip()
    }
    
    # Publish to RabbitMQ
    channel.basic_publish(
        exchange='',
        routing_key='jobs_queue',
        body=json.dumps(job_payload),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent (saves to disk)
        )
    )
    connection.close()

# --- 2. THE CONSUMER (AI Worker) ---
def ai_worker():
    """
    CONSUMER: Connects to RabbitMQ, listens for jobs, and processes them.
    This could eventually be moved to a completely separate server!
    """
    connection, channel = get_rabbitmq_channel()
    print(" [*] AI Worker waiting for jobs in RabbitMQ. To exit press CTRL+C")

    def callback(ch, method, properties, body):
        job = json.loads(body)
        print("-" * 50)
        print(f"🤖 AI Processing: {job['title']} at {job['company']}")
        
        # Simulate AI processing (e.g., Gemini API call)
        
        
        final_result = ai_scorer.evaluate_job(job_title=job['title'], job_description=job['description'])
        # AI Scorer returns verdicts like "Strong Match", "Partial Match", "Poor Match"
        if "Match" in final_result.get("verdict", "") and final_result.get("verdict") != "Poor Match":
            
            print("✅ PASSED AI + DETERMINISTIC FILTER!")
            print(f"   Score: {final_result['ai_score']}")
            print(f"   Verdict: {final_result['verdict']}")
            print(f"   Apply Link: {job['link']}")
        
            # TODO NEXT: Pass this job to PostgreSQL or notify user
        
        else:
            # It's a REJECTED or POOR MATCH. We drop it and move on.
            reason = final_result.get('reason') or ", ".join(final_result.get('red_flags', [])) or "Poor Match / Low Score"
            print(f"❌ DROPPED: {reason}")
        
        # Acknowledge the message so RabbitMQ removes it from the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # prefetch_count=1 tells RabbitMQ not to give more than one message to a worker at a time
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='jobs_queue', on_message_callback=callback)
    
    # Start listening continuously
    channel.start_consuming()

if __name__ == "__main__":
    print("Initializing Distributed Job Matching Pipeline...")
    
    # 1. Start the AI Consumer in a background thread
    worker_thread = threading.Thread(target=ai_worker, daemon=True)
    worker_thread.start()
    
    try:
        # 2. Start the Scraper (Producer) on the main thread
        run_scraper(on_job_found_callback=process_job)
        
    except Exception as e:
        print(f"Pipeline crashed: {e}")