from psycopg2.errors import TooManyColumns
from asyncio import base_events
import psycopg2
from psycopg2.extras import Json
import math
import os


class DatabaseManager:
    def __init__ (self):
        """Initialize the databse connection. """
        try:
            self.connection = psycopg2.connect(
                host = os.getenv("DB_HOST"),
                database = os.getenv("DB_NAME"),
                user = os.getenv("DB_USER"),
                password =  os.getenv("DB_PASSWORD")
            )
            self.connection.autocommit = True
            print(" Database connection successfuly established.")

        except psycopg2.Error as e:
            print(f"Database connection failed: {e}")
            raise e

    def create_table(self):
        """Creates an Table with the job values"""
        query =  """
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255) NOT NULL,
            link TEXT UNIQUE NOT NULL, -- UNIQUE constraint is crucial for upserts
            description TEXT,
            ai_score INTEGER DEFAULT 0,
            date_posted DATE,
            verdict VARCHAR(50),
            is_applied BOOLEAN,
            missing_skills JSONB DEFAULT '[]'::jsonb,
            red_flags JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.connection.cursor() as cur:
            cur.execute(query)
            # Safe database migration: Add date_posted column if it doesn't already exist
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS date_posted DATE;")
            cur.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_applied BOOLEAN;")
            print("Database tables verified.")


    def upsert_job(self,raw_job_data: dict, ai_result: dict):
        """It will add the jobs to the DB"""
        query = """
        INSERT INTO jobs (title, company, link, description, ai_score, verdict, missing_skills, red_flags, date_posted)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (link) 
        DO UPDATE SET 
            ai_score = EXCLUDED.ai_score,
            verdict = EXCLUDED.verdict,
            missing_skills = EXCLUDED.missing_skills,
            red_flags = EXCLUDED.red_flags,
            date_posted = EXCLUDED.date_posted,
            updated_at = CURRENT_TIMESTAMP;
        """
        values = (
            raw_job_data.get("title"),
            raw_job_data.get("company"),
            raw_job_data.get("link"),
            raw_job_data.get("description"),
            ai_result.get("ai_score", 0),
            ai_result.get("verdict", "Unknown"),
            Json(ai_result.get("missing_skills", [])),
            Json(ai_result.get("red_flags", [])),
            raw_job_data.get("date_posted") or None
        )
        try:
          with self.connection.cursor() as cur:
            cur.execute(query,values)
            print("Job upserted in database.")
        except Exception as e:
            print(f"Failed to insert job into DB: {e}")
    
    def close(self):
        """Closes the database connection cleanly."""
        if self.connection:
            self.connection.close()
    def job_exists(self,link:str)-> bool :
        query = "SELECT 1 FROM jobs WHERE link = %s"
        try:
            with self.connection.cursor() as cur:
                cur.execute(query,(link,))
                # cur does not return anything it just store the result in cur object 
                #  which we can retrieve after using one of the cur function like fetchall fetchone
                return cur.fetchone() is not None
        except Exception as e:
            print(f"Error checking if job exists: {e}")
            return False
                    


    def fetch_jobs(self, min_score: int = 0, limit: int = 1, offset: int = 0, verdict: str = None, sort_by: str = "created_at"):
        """Fetch jobs from the database based on AI score and verdict."""
        # Determine the sorting column to prevent SQL injection and dynamic parameter issues
        if sort_by == "score":
            order_column = "ai_score"
        else:
            order_column = "created_at"

        query_conditions = ["ai_score >= %s"]
        params = [min_score]

        if verdict:
            query_conditions.append("verdict = %s")
            params.append(verdict)

        conditions_str = " AND ".join(query_conditions)

        query = f"""
        SELECT id, title, company, link, description, ai_score, verdict, missing_skills, red_flags, created_at, date_posted 
        FROM jobs
        WHERE {conditions_str}
        ORDER BY {order_column} DESC LIMIT %s OFFSET %s
        """
        select_params = params + [limit, offset]

        query2 = f"SELECT COUNT(*) FROM jobs WHERE {conditions_str}"
        count_params = params

        try:
            with self.connection.cursor() as cur:
                cur.execute(query2, count_params)
                total_count = cur.fetchone()[0]

                pages = math.ceil(total_count / limit) if total_count > 0 else 0
                cur.execute(query, select_params)
                columns = [col[0] for col in cur.description]
                result = []
                for row in cur.fetchall():
                    result.append(dict(zip(columns, row)))
                return {
                    "total_count": total_count,
                    "pages": pages,
                    "jobs": result
                }
        except Exception as e:
            print(f"Failed to fetch jobs: {e}")
            return {
                "total_count": 0,
                "pages": 0,
                "jobs": []
            }
    
    def fetch_jobs_by_id(self,job_id:int):
        """Fetch a specific job by its ID"""
        query =  """ SELECT id, title, company, link, description, ai_score, verdict, missing_skills, red_flags, created_at, date_posted 
        FROM jobs
        WHERE id = %s
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(query, (job_id,))
                # Why it fails: (job_id) is treated as a regular integer in parentheses, not a tuple. psycopg2 expects a tuple/sequence.
                #  Fix: Add a trailing comma to make it a tuple:

                columns = [col[0] for col in cur.description]
                row = cur.fetchone()
                if row:
                    return dict(zip(columns,row))
                return None
        except Exception as e:
            print(f"Failed to fetch job by ID: {e}")
            return None                