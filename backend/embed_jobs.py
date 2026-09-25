"""Backfill saved jobs and process pending jobs into pgvector storage."""
import argparse
import logging
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

from db.repositories.raw_jobs import RawJobRepository
from db.repositories.processed_jobs import ProcessedJobRepository
from processing.pipeline import JobProcessor, ProcessingStats
from processing.stages.embed import FastEmbedEncoder, JobEmbedder
from processing.stages.extract import JobExtractor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    load_dotenv(Path(__file__).with_name('.env'))
    logging.basicConfig(level=logging.INFO)
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'), connect_timeout=10,
    )
    try:
        raw = RawJobRepository(conn)
        processed = ProcessedJobRepository(conn)
        raw.create_table()
        processed.create_table()
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('jobs')")
            if cur.fetchone()[0] is not None:
                cur.execute('''
                    INSERT INTO raw_jobs (title, company, link, description, date_posted)
                    SELECT title, company, link, description, date_posted FROM jobs
                    ON CONFLICT (link) DO NOTHING
                ''')
            if args.retry_failed:
                cur.execute("UPDATE raw_jobs SET status='pending', error=NULL WHERE status='failed'")
        conn.commit()
        jobs = raw.fetch_pending(args.limit)
        if not jobs:
            print('No pending jobs. Run the scraper first, then run this command again.')
            return
        processor = JobProcessor(conn, raw, processed, JobExtractor(), JobEmbedder(FastEmbedEncoder()))
        stats = ProcessingStats()
        for job in jobs:
            stats.bump(processor.process_one(job))
        print(stats.as_dict())
        if stats.failed:
            raise SystemExit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
