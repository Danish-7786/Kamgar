from processing.normalization.seniority import normalize_seniority
from processing.normalization.skills import normalize_skill, normalize_skills
from processing.schemas import (
    EducationLevel,
    EmploymentType,
    ExtractedJob,
    ProcessedJob,
    RawSalary,
    RemoteType,
    SalaryPeriod,
    Seniority,
)
from processing.stages.normalize import normalize


# --- skills --------------------------------------------------------------- #
def test_skill_alias_mapping():
    assert normalize_skill("NodeJS") == "Node.js"
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("golang") == "Go"


def test_unknown_skill_kept_as_is():
    assert normalize_skill("  Elixir ") == "Elixir"


def test_skills_dedupe_after_aliasing():
    # NodeJS and Node.js both canonicalize to Node.js -> one entry.
    assert normalize_skills(["NodeJS", "Node.js", "node js"]) == ["Node.js"]


# --- seniority ------------------------------------------------------------ #
def test_seniority_folds_to_entry():
    for raw in ("Junior", "Graduate", "Trainee", "fresher"):
        assert normalize_seniority(raw) is Seniority.ENTRY


def test_seniority_known_and_unknown():
    assert normalize_seniority("Senior") is Seniority.SENIOR
    assert normalize_seniority("wizard") is Seniority.UNKNOWN
    assert normalize_seniority(None) is Seniority.UNKNOWN


# --- full stage ----------------------------------------------------------- #
def _extracted(**kwargs) -> ExtractedJob:
    base = {"role": "Backend Engineer", "seniority": "Junior", "skills": ["NodeJS"]}
    base.update(kwargs)
    return ExtractedJob(**base)


def test_normalize_returns_strict_processed_job():
    result = normalize(_extracted())
    assert isinstance(result, ProcessedJob)
    assert result.seniority is Seniority.ENTRY
    assert result.skills == ["Node.js"]


def test_normalize_maps_categoricals():
    job = normalize(
        _extracted(remote="wfh", employment_type="full time", education="b.tech")
    )
    assert job.remote is RemoteType.REMOTE
    assert job.employment_type is EmploymentType.FULL_TIME
    assert job.education is EducationLevel.BACHELORS


def test_normalize_salary():
    job = normalize(
        _extracted(salary=RawSalary(min_amount=10, max_amount=20, currency="inr", period="per annum"))
    )
    assert job.salary.period is SalaryPeriod.YEARLY
    assert job.salary.currency == "INR"


def test_unknown_categoricals_degrade_to_unknown():
    job = normalize(_extracted(remote="teleport", employment_type=None, education="wizardry"))
    assert job.remote is RemoteType.UNKNOWN
    assert job.employment_type is EmploymentType.UNKNOWN
    assert job.education is EducationLevel.UNKNOWN


def test_role_optional_for_skills_only_job():
    job = normalize(ExtractedJob(role=None, skills=["Go"]))
    assert job.role is None
    assert job.skills == ["Go"]


def test_responsibilities_stripped_and_emptied():
    job = normalize(_extracted(responsibilities=["  Build APIs ", "", "   "]))
    assert job.responsibilities == ["Build APIs"]
