"""Module 4: rule validation.

Pure backstop for the AI extractor. Cleans recoverable issues in an
``ExtractedJob`` and rejects only jobs that cannot be matched or embedded.
No I/O. Returns a NEW ExtractedJob (never mutates the input).
"""

from __future__ import annotations

from typing import Optional

from processing.schemas import ExtractedJob, RawSalary


class ValidationRejection(Exception):
    """Raised when a job is unusable and should be quarantined, not stored."""


# A *candidate* requirement above this many years is almost certainly company
# age / "N years in business" that leaked in — the "30 years" trap. We null it
# instead of trusting it. Realistic senior requirements sit well under this.
MAX_REALISTIC_EXPERIENCE = 25

# A "skill" longer than this is a sentence, not a technology.
MAX_SKILL_LEN = 50
# Guard against a runaway list blowing up the embedding text.
MAX_SKILLS = 50


def _clean_skill_list(skills: list[str]) -> list[str]:
    """Strip, drop empties/sentences, de-dupe case-insensitively (keeping the
    first spelling — normalization fixes casing later), and cap the count."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in skills:
        if not isinstance(raw, str):
            continue
        s = raw.strip()
        if not s or len(s) > MAX_SKILL_LEN:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out[:MAX_SKILLS]


def _sane_experience(value: Optional[int]) -> Optional[int]:
    """Null out negatives and above-ceiling values (leaked company age)."""
    if value is None:
        return None
    if value < 0 or value > MAX_REALISTIC_EXPERIENCE:
        return None
    return value


def _clean_salary(salary: Optional[RawSalary]) -> Optional[RawSalary]:
    if salary is None:
        return None
    min_a = salary.min_amount if (salary.min_amount is None or salary.min_amount >= 0) else None
    max_a = salary.max_amount if (salary.max_amount is None or salary.max_amount >= 0) else None
    # Inverted range: trust the floor, drop the ceiling.
    if min_a is not None and max_a is not None and max_a < min_a:
        max_a = None
    # Nothing useful left -> drop the salary object entirely.
    if min_a is None and max_a is None and not salary.currency:
        return None
    return salary.model_copy(update={"min_amount": min_a, "max_amount": max_a})


def validate(job: ExtractedJob) -> ExtractedJob:
    """Sanitize an ExtractedJob; raise ValidationRejection if unusable."""
    role = job.role.strip() if (job.role and job.role.strip()) else None
    skills = _clean_skill_list(job.skills)
    nice = _clean_skill_list(job.nice_to_have_skills)

    exp_min = _sane_experience(job.experience_min_years)
    exp_max = _sane_experience(job.experience_max_years)
    if exp_min is not None and exp_max is not None and exp_max < exp_min:
        exp_max = None  # trust the floor

    salary = _clean_salary(job.salary)

    # Reject only when there is nothing to match on or embed.
    if role is None and not skills:
        raise ValidationRejection("no role and no skills — nothing to match or embed")

    return job.model_copy(
        update={
            "role": role,
            "skills": skills,
            "nice_to_have_skills": nice,
            "experience_min_years": exp_min,
            "experience_max_years": exp_max,
            "salary": salary,
        }
    )
