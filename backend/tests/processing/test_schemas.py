import pytest
from pydantic import ValidationError

from processing.schemas import (
    EducationLevel,
    EmploymentType,
    ExtractedJob,
    ProcessedJob,
    RemoteType,
    Salary,
    Seniority,
)


# --- ExtractedJob: permissive, mirrors messy LLM output ------------------- #
def test_extracted_job_accepts_empty_input():
    """The LLM may find nothing; that must not crash extraction."""
    job = ExtractedJob()
    assert job.role is None
    assert job.skills == []


def test_extracted_job_keeps_raw_unnormalized_values():
    """Raw values like 'Junior' / 'NodeJS' are allowed here — normalization
    happens in a later stage, not at extraction."""
    job = ExtractedJob(seniority="Junior", skills=["NodeJS"])
    assert job.seniority == "Junior"
    assert job.skills == ["NodeJS"]


def test_extracted_job_ignores_unknown_llm_keys():
    """A hallucinated extra field is dropped, not fatal."""
    job = ExtractedJob(role="Backend Engineer", made_up_field="oops")
    assert job.role == "Backend Engineer"
    assert not hasattr(job, "made_up_field")


# --- ProcessedJob: strict canonical form ---------------------------------- #
def test_processed_job_requires_normalized_enum():
    """A raw 'Junior' can never become a ProcessedJob — the enum is the
    guarantee that only normalized data is persisted."""
    with pytest.raises(ValidationError):
        ProcessedJob(role="Backend Engineer", seniority="Junior", skills=["Node.js"])


def test_processed_job_valid():
    job = ProcessedJob(
        role="Backend Engineer",
        seniority=Seniority.ENTRY,
        skills=["Node.js", "PostgreSQL"],
        remote=RemoteType.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        education=EducationLevel.BACHELORS,
    )
    assert job.seniority is Seniority.ENTRY
    assert job.remote is RemoteType.REMOTE


def test_processed_job_defaults_to_unknown_enums():
    """Missing enum fields degrade to UNKNOWN rather than failing."""
    job = ProcessedJob(role="X", seniority=Seniority.MID, skills=[])
    assert job.remote is RemoteType.UNKNOWN
    assert job.employment_type is EmploymentType.UNKNOWN
    assert job.education is EducationLevel.UNKNOWN


def test_processed_job_rejects_inverted_experience_range():
    with pytest.raises(ValidationError):
        ProcessedJob(
            role="X",
            seniority=Seniority.SENIOR,
            skills=[],
            experience_min_years=5,
            experience_max_years=2,
        )


def test_processed_job_rejects_absurd_experience():
    """ge/le bounds catch a hallucinated '99 years required'."""
    with pytest.raises(ValidationError):
        ProcessedJob(
            role="X", seniority=Seniority.MID, skills=[], experience_min_years=99
        )


# --- Salary --------------------------------------------------------------- #
def test_salary_rejects_inverted_range():
    with pytest.raises(ValidationError):
        Salary(min_amount=100, max_amount=50)


def test_salary_valid_range():
    s = Salary(min_amount=50, max_amount=100, currency="INR")
    assert s.max_amount == 100
