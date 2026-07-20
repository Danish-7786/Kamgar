
from typing import Optional

from psycopg2.extras import Json, RealDictCursor

RAW_JOBS_DDL = """
CREATE TABLE IF NOT EXISTS raw_jobs(
  id            SERIAL PRIMARY KEY,
    source        VARCHAR(50),
    external_id   TEXT,
    title         TEXT,
    company       TEXT,
    link          TEXT UNIQUE NOT NULL,          -- dedupe at ingestion
    description   TEXT,
    location      TEXT,
    date_posted   DATE,
    raw_payload   JSONB,                          -- full original row, for re-processing
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending|processed|failed
    error         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at  TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_status ON raw_jobs(status);
"""



class RawJobRepository:
    def __init__(self,connnection):
        self.conn = connnection

    def create_table(self):
        with self.conn.cursor() as cur:
            cur.execute(RAW_JOBS_DDL)
    
    def insert(self,*, source, external_id, title, company,link, description, location, date_posted, raw_payload) -> Optional[int]:
        """Insert one scraped job. Returns its id, or None if the link already
        exists (deduped). ON CONFLICT DO NOTHING is the ingestion-side guard."""
        sql = """
        INSERT INTO raw_jobs (source, external_id, title, company, link,
                              description, location, date_posted, raw_payload)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (link) DO NOTHING
        RETURNING id;
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (source, external_id, title, company, link,
                              description, location, date_posted, Json(raw_payload)))
            row = cur.fetchone()
            return row[0] if row else None


    def fetch_pending(self, limit: int = 50) -> list[dict]:
        """The work-queue query — fast, index-backed."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM raw_jobs WHERE status = 'pending' "
                "ORDER BY created_at LIMIT %s;",
                (limit,),
            )
            return list(cur.fetchall())
    def mark_processed(self, raw_id: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE raw_jobs SET status='processed', processed_at=CURRENT_TIMESTAMP, "
                "error=NULL WHERE id=%s;", (raw_id,))

    def mark_failed(self, raw_id: int, error: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE raw_jobs SET status='failed', error=%s WHERE id=%s;",
                (error[:1000], raw_id))

            