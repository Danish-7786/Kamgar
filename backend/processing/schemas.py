"""
The data contract for Phase 2 (AI job processing).

Two models, on purpose:

  * ``ExtractedJob``  -> the *untrusted* shape the LLM returns. Permissive:
                         fields may be missing, seniority is free text
                         ("Junior"), skills are raw ("NodeJS"). Nothing here
                         is guaranteed to be normalized yet.

  * ``ProcessedJob``  -> the *canonical* shape after validation + normalization.
                         Strict: seniority is an enum, ranges are sane. This is
                         what we persist to ``processed_jobs`` and embed.

The pipeline moves data from the first shape to the second:

    extract() -> ExtractedJob  ->  validate()  ->  normalize() -> ProcessedJob

Keeping the shapes distinct means an un-normalized value (e.g. "Junior")
literally cannot be constructed as a ProcessedJob — the type is the guarantee.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------------------------------- #
# Normalized enums — the canonical vocabulary. Normalization (Module 5) maps
# messy real-world values onto these. Every enum has UNKNOWN so the pipeline
# degrades gracefully instead of throwing away an otherwise-good job.
# --------------------------------------------------------------------------- #
class Seniority(str, Enum):
    ENTRY = "Entry"        # Junior, Graduate, Trainee, Associate all fold to here
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"
    UNKNOWN = "Unknown"


class EmploymentType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    TEMPORARY = "Temporary"
    UNKNOWN = "Unknown"


class RemoteType(str, Enum):
    ONSITE = "Onsite"
    HYBRID = "Hybrid"
    REMOTE = "Remote"
    UNKNOWN = "Unknown"


class EducationLevel(str, Enum):
    NONE = "None"          # no formal requirement stated
    DIPLOMA = "Diploma"
    BACHELORS = "Bachelors"
    MASTERS = "Masters"
    PHD = "PhD"
    UNKNOWN = "Unknown"


class SalaryPeriod(str, Enum):
    HOURLY = "Hourly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"
    UNKNOWN = "Unknown"


# --------------------------------------------------------------------------- #
# Salary — structured, never a free-text string. A number you can filter and
# sort on is worth far more than "₹12-18 LPA" trapped in prose.
# --------------------------------------------------------------------------- #
class Salary(BaseModel):
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    period: SalaryPeriod = SalaryPeriod.UNKNOWN

    @model_validator(mode="after")
    def _check_range(self) -> "Salary":
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.max_amount < self.min_amount
        ):
            raise ValueError("salary max_amount cannot be less than min_amount")
        return self


# --------------------------------------------------------------------------- #
# RawSalary — the permissive salary shape the LLM fills. `period` is free text
# ("yearly", "per annum", "monthly"); normalization maps it to SalaryPeriod.
# Keeping this separate from Salary is why a messy period string can't blow up
# the whole extraction.
# --------------------------------------------------------------------------- #
class RawSalary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None


# --------------------------------------------------------------------------- #
# ExtractedJob — the LLM's raw output. Permissive by design.
#   * every field optional, because the model may not find it
#   * seniority / employment_type / remote are plain strings here — they get
#     mapped to enums during normalization, NOT at extraction time
#   * extra="ignore": if the LLM invents a key, drop it instead of crashing
# --------------------------------------------------------------------------- #
class ExtractedJob(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: Optional[str] = None
    seniority: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)

    # Candidate experience the ROLE requires — never company age / "founded in".
    # See Module 4 (validation) for how we defend this invariant.
    experience_min_years: Optional[int] = None
    experience_max_years: Optional[int] = None

    salary: Optional[RawSalary] = None
    location: Optional[str] = None
    remote: Optional[str] = None
    employment_type: Optional[str] = None
    education: Optional[str] = None
    domain: Optional[str] = None
    responsibilities: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# ProcessedJob — the canonical, validated, normalized record. Strict.
# This is what we store in `processed_jobs` and what feeds the embedding.
# --------------------------------------------------------------------------- #
class ProcessedJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Optional: validation (Module 4) permits a skills-only job with no role.
    role: Optional[str] = None
    seniority: Seniority
    skills: list[str]
    nice_to_have_skills: list[str] = Field(default_factory=list)

    experience_min_years: Optional[int] = Field(default=None, ge=0, le=60)
    experience_max_years: Optional[int] = Field(default=None, ge=0, le=60)

    salary: Optional[Salary] = None
    location: Optional[str] = None
    remote: RemoteType = RemoteType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    education: EducationLevel = EducationLevel.UNKNOWN
    domain: Optional[str] = None
    responsibilities: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_experience_range(self) -> "ProcessedJob":
        if (
            self.experience_min_years is not None
            and self.experience_max_years is not None
            and self.experience_max_years < self.experience_min_years
        ):
            raise ValueError(
                "experience_max_years cannot be less than experience_min_years"
            )
        return self
