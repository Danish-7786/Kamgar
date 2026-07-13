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
                    


    def fetch_jobs(self, min_score:int = 0,limit:int=1,offset:int=0,verdict:str = None):
        """Fetch jobs from the database based on AI score and verdict."""
        query = """
        SELECT id, title,company,link,description,ai_score,verdict,missing_skills,red_flags,created_at 
        FROM jobs
        WHERE ai_score >= %s
        ORDER BY ai_score DESC LIMIT %s OFFSET %s
        """
        params = [min_score,limit,offset]

        query2= """SELECT COUNT(*) FROM jobs where ai_score>= %s"""
        params2=[min_score]
        try:
            with self.connection.cursor() as cur:
                cur.execute(query2,(min_score,))
                total_count = cur.fetchone()[0]

                pages = math.ceil(total_count / limit) if total_count > 0 else 0
                cur.execute(query,params)
                columns = [col[0] for col in cur.description]
                result = []
                for row in cur.fetchall():
                    result.append(dict(zip(columns,row)))
                    # zip -> bounds the attribute to the value 
                    # {cols : "name","age"}
                    # {values : "Anjan", 23 };
                    # after zip 
                    # {"name":"danish","Age":23}
                return {
                    "total_count":total_count,
                    "pages":pages,
                    "jobs":result
                }
        except Exception as e:
            print(f"Failed to fetch a jobs: {e}")
            return {
                "total_count": 0,
                "pages": 0,
                "jobs": []
                }
    
    def fetch_jobs_by_id(self,job_id:int):
        """Fetch a specific job by its ID"""
        query =  """ SELECT id, title, company, link, description, ai_score, verdict, missing_skills, red_flags, created_at 
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