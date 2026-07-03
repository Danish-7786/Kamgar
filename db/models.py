from asyncio import base_events
import psycopg2
from psycopg2.extras import Json

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
            verdict VARCHAR(50),
            missing_skills JSONB DEFAULT '[]'::jsonb,
            red_flags JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.connection.cursor() as cur:
            cur.execute(query)
            print("Database tables verified.")


    def upsert_job(self,raw_job_data: dict, ai_result: dict):
        """It will add the jobs to the DB"""
        query = """
        INSERT INTO jobs (title, company, link, description, ai_score, verdict, missing_skills, red_flags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (link) 
        DO UPDATE SET 
            ai_score = EXCLUDED.ai_score,
            verdict = EXCLUDED.verdict,
            missing_skills = EXCLUDED.missing_skills,
            red_flags = EXCLUDED.red_flags,
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
            Json(ai_result.get("red_flags", []))
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


