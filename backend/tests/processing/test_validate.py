import pytest

from processing.schemas import ExtractedJob, RawSalary
from processing.stages.validate import (
    MAX_REALISTIC_EXPERIENCE,
    ValidationRejection,
    validate,
)


def _job(**kwargs) -> ExtractedJob:
    base = {"role": "Backend Engineer", "skills": ["Node.js"]}
    base.update(kwargs)
    return ExtractedJob(**base)


# --- the experience guard (the "30 years" trap) --------------------------- #
def test_absurd_experience_is_nulled_not_trusted():
    job = validate(_job(experience_min_years=30))
    assert job.experience_min_years is None


def test_realistic_experience_is_kept():
    job = validate(_job(experience_min_years=5, experience_max_years=8))
    assert (job.experience_min_years, job.experience_max_years) == (5, 8)


def test_boundary_experience_kept_at_ceiling():
    job = validate(_job(experience_min_years=MAX_REALISTIC_EXPERIENCE))
    assert job.experience_min_years == MAX_REALISTIC_EXPERIENCE


def test_negative_experience_is_nulled():
    assert validate(_job(experience_min_years=-3)).experience_min_years is None


def test_inverted_experience_range_drops_max():
    job = validate(_job(experience_min_years=5, experience_max_years=2))
    assert job.experience_min_years == 5 and job.experience_max_years is None


# --- skill hygiene -------------------------------------------------------- #
def test_skills_are_stripped_deduped_and_emptied():
    job = validate(_job(skills=["  Node.js ", "node.js", "", "  ", "PostgreSQL"]))
    assert job.skills == ["Node.js", "PostgreSQL"]


def test_sentence_length_skill_is_dropped():
    long_skill = "x" * 100
    job = validate(_job(skills=["Python", long_skill]))
    assert job.skills == ["Python"]


# --- salary sanity -------------------------------------------------------- #
def test_negative_salary_is_nulled():
    job = validate(_job(salary=RawSalary(min_amount=-1, max_amount=100)))
    assert job.salary.min_amount is None and job.salary.max_amount == 100


def test_inverted_salary_drops_max():
    job = validate(_job(salary=RawSalary(min_amount=100, max_amount=50)))
    assert job.salary.min_amount == 100 and job.salary.max_amount is None


def test_empty_salary_object_is_dropped():
    job = validate(_job(salary=RawSalary()))
    assert job.salary is None


# --- reject contract ------------------------------------------------------ #
def test_reject_when_no_role_and_no_skills():
    with pytest.raises(ValidationRejection):
        validate(ExtractedJob(role="   ", skills=[]))


def test_role_only_is_kept():
    job = validate(ExtractedJob(role="Data Scientist", skills=[]))
    assert job.role == "Data Scientist"


def test_skills_only_is_kept():
    job = validate(ExtractedJob(role=None, skills=["Go"]))
    assert job.skills == ["Go"]


# --- immutability --------------------------------------------------------- #
def test_input_is_not_mutated():
    original = _job(skills=["  Node.js ", "node.js"], experience_min_years=30)
    validate(original)
    assert original.skills == ["  Node.js ", "node.js"]
    assert original.experience_min_years == 30
