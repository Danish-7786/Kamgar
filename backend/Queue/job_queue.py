import pika
import json
import threading
import time

from linkedin_jobs_scraper.events import EventData
from scorer.deterministic_job_scrorer import DeterministicJobScorer

from db.jobs import DatabaseManager


from scorer.ai_scorer import AIScorer


# Initialize the deterministic filter globally
job_filter = DeterministicJobScorer()

# --- RABBITMQ CONNECTION SETUP ---
def get_rabbitmq_channel():
    # Assumes RabbitMQ is running locally via Docker
    parameters = pika.ConnectionParameters(host='localhost', heartbeat=0)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    # durable=True ensures the queue survives a RabbitMQ restart
    channel.queue_declare(queue='jobs_queue', durable=True)
    return connection, channel

# --- 1. THE PRODUCER (Scraper) ---
def process_job(title: str,date_posted:str, company: str, link: str, description: str):
    """
    PRODUCER: This callback pre-filters the job, and if it passes, publishes to RabbitMQ.
    """
    clean_desc = description.replace('\n', ' ').strip()
   
    
    # Run the fast, free regex filter first
    result = job_filter.score_job(title=title, description=clean_desc)
    print("result",result)
    if result["verdict"] == "REJECTED":
        print(f"[REJECTED] DROPPED ({title}): {result['reason']}")
        return # Exit early, don't send to queue!
    print(("-")*50)
    print(f"Scraper found MATCH: {title} - Publishing to RabbitMQ...")
    
    # We need a new connection per thread in pika
    connection, channel = get_rabbitmq_channel()
    
    # Create a simple dictionary payload
    job_payload = {
        "title": title,
        "company": company,
        "link": link,
        "date_posted":date_posted,
        "description": description
    }
    print(f"job date ${job_payload['date_posted']}")
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


def process_linkedin_job(data: EventData):
    """
    Wrapper for LinkedIn scraper EventData callback, forwarding parameters to process_job.
    """
    process_job(
        title=data.title,
        company=data.company,
        link=data.link,
        description=data.description
    )


# --- 2. THE CONSUMER (AI Worker) ---
def ai_worker():
    """
    CONSUMER: Connects to RabbitMQ, listens for jobs, and processes them.
    This could eventually be moved to a completely separate server!
    """
    print("Initializing Database Connection and AI Scorer inside worker thread...")
    db_client = DatabaseManager()
    db_client.create_table()
    ai_scorer = AIScorer()
    
    connection, channel = get_rabbitmq_channel()
    print(" [*] AI Worker waiting for jobs in RabbitMQ. To exit press CTRL+C")

    def callback(ch, method, properties, body):
        job = json.loads(body)
        print("-" * 80)
        
        
        if db_client.job_exists(job["link"]):
            print(f"[DUPLICATE] URL already exists in DB. Skipping: {job['title']} at {job['company']}")
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return
        print(f"AI Processing: {job['title']} at {job['company']}")
        
        final_result = ai_scorer.evaluate_job(job_title=job['title'], job_description=job['description'])
        # AI Scorer returns verdicts like "Strong Match", "Partial Match", "Poor Match"
        if "Match" in final_result.get("verdict", "") and final_result.get("verdict") != "Poor Match":
            print("PASSED AI + DETERMINISTIC FILTER!")
            print(f"   Score: {final_result['ai_score']}")
            print(f"   Verdict: {final_result['verdict']}")
            print(f"   Apply Link: {job['link']}")
            db_client.upsert_job(raw_job_data=job,ai_result=final_result)
        else:
            # It's a REJECTED or POOR MATCH. We drop it and move on.
            reason = final_result.get('reason') or ", ".join(final_result.get('red_flags', [])) or "Poor Match / Low Score"
            print(f"[REJECTED] DROPPED: {reason}")
        
        # Acknowledge the message so RabbitMQ removes it from the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
        # Rate-limiting: sleep 5 seconds to stay under the Gemini API Free Tier limit (15 Requests Per Minute)
        time.sleep(5)

    # prefetch_count=1 tells RabbitMQ not to give more than one message to a worker at a time
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='jobs_queue', on_message_callback=callback)
    
    # Start listening continuously
    channel.start_consuming()

