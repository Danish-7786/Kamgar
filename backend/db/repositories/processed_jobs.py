from __future__ import annotations

from typing import Optional

from psycopg2.extras import Json

from processing.schemas import ProcessedJob
PROCESSED_JOBS_DDL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS processed_jobs (
    id                        SERIAL PRIMARY KEY,
    raw_job_id                INTEGER NOT NULL UNIQUE
                                  REFERENCES raw_jobs(id) ON DELETE CASCADE,  -- 1:1, "process once"
    role                      TEXT,
    seniority                 VARCHAR(20),
    skills                    JSONB NOT NULL DEFAULT '[]'::jsonb,
    nice_to_have_skills       JSONB NOT NULL DEFAULT '[]'::jsonb,
    experience_min_years      INTEGER,
    experience_max_years      INTEGER,
    salary                    JSONB,
    location                  TEXT,
    remote                    VARCHAR(20),
    employment_type           VARCHAR(20),
    education                 VARCHAR(20),
    domain                    TEXT,
    responsibilities          JSONB NOT NULL DEFAULT '[]'::jsonb,
    embedding                 vector(384),
    embedding_recipe_version  INTEGER,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
# Run once AFTER you have a few thousand rows (see note below).
PROCESSED_JOBS_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_processed_jobs_embedding "
    "ON processed_jobs USING hnsw (embedding vector_cosine_ops);"
)

def serialize_processed(job: ProcessedJob) -> dict:
    """PURE: ProcessedJob -> column values (enums -> str, salary -> dict)."""
    return {
        "role": job.role,
        "seniority": job.seniority.value,
        "skills": job.skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "experience_min_years": job.experience_min_years,
        "experience_max_years": job.experience_max_years,
        "salary": job.salary.model_dump(mode="json") if job.salary else None,
        "location": job.location,
        "remote": job.remote.value,
        "employment_type": job.employment_type.value,
        "education": job.education.value,
        "domain": job.domain,
        "responsibilities": job.responsibilities,
    }


def to_pgvector_literal(vec: list[float]) -> str:
    """PURE: [0.1, 0.2] -> '[0.1,0.2]' (pgvector's text input format)."""
    return "[" + ",".join(str(float(x)) for x in vec) + "]"

class ProcessedJobRepository:
    def __init__(self, connection):
        self.conn = connection

    def create_table(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(PROCESSED_JOBS_DDL)

    def insert(self, raw_job_id: int, job: ProcessedJob,embedding: list[float], recipe_version: int) -> Optional[int]:
        """Store the processed job. Returns id, or None if this raw_job_id was"""
        c = serialize_processed(job)
        sql = """
        INSERT INTO processed_jobs (
            raw_job_id, role, seniority, skills, nice_to_have_skills,
            experience_min_years, experience_max_years, salary, location,
            remote, employment_type, education, domain, responsibilities,
            embedding, embedding_recipe_version
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s)
        ON CONFLICT (raw_job_id) DO NOTHING
        RETURNING id;
        """
        params = (
            raw_job_id,c["role"], c["seniority"], Json(c["skills"]),
            Json(c["nice_to_have_skills"]), c["experience_min_years"],
            c["experience_max_years"],
            Json(c["salary"]) if c["salary"] is not None else None,
            c["location"], c["remote"], c["employment_type"], c["education"],
            c["domain"], Json(c["responsibilities"]),
            to_pgvector_literal(embedding), recipe_version,
        )
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None