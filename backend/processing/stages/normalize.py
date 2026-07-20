"""Module 5: normalization.

Crosses from the permissive ``ExtractedJob`` to the strict canonical
``ProcessedJob``: maps free-text values onto enums and canonicalizes skills.
Expects an already-validated ExtractedJob (Module 4) as input.
"""

from __future__ import annotations

from typing import Optional

from processing.normalization.mappings import (
    normalize_education,
    normalize_employment_type,
    normalize_remote,
    normalize_salary_period,
)
from processing.normalization.seniority import normalize_seniority
from processing.normalization.skills import normalize_skills
from processing.schemas import ExtractedJob, ProcessedJob, RawSalary, Salary


def _normalize_salary(raw: Optional[RawSalary]) -> Optional[Salary]:
    if raw is None:
        return None
    return Salary(
        min_amount=raw.min_amount,
        max_amount=raw.max_amount,
        currency=raw.currency.strip().upper() if raw.currency else None,
        period=normalize_salary_period(raw.period),
    )


def normalize(job: ExtractedJob) -> ProcessedJob:
    return ProcessedJob(
        role=job.role.strip() if job.role else None,
        seniority=normalize_seniority(job.seniority),
        skills=normalize_skills(job.skills),
        nice_to_have_skills=normalize_skills(job.nice_to_have_skills),
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
        salary=_normalize_salary(job.salary),
        location=job.location.strip() if job.location else None,
        remote=normalize_remote(job.remote),
        employment_type=normalize_employment_type(job.employment_type),
        education=normalize_education(job.education),
        domain=job.domain.strip() if job.domain else None,
        responsibilities=[r.strip() for r in job.responsibilities if r and r.strip()],
    )
