"""Categorical normalization for the remaining enum fields.

One generic ``_map`` helper + one alias table per field. Every mapping falls
back to the field's UNKNOWN member, so an unrecognized value degrades
gracefully rather than raising.
"""

from __future__ import annotations

from typing import TypeVar

from processing.schemas import (
    EducationLevel,
    EmploymentType,
    RemoteType,
    SalaryPeriod,
)

_E = TypeVar("_E")

EMPLOYMENT_TYPE_ALIASES: dict[str, EmploymentType] = {
    "full time": EmploymentType.FULL_TIME,
    "full-time": EmploymentType.FULL_TIME,
    "fulltime": EmploymentType.FULL_TIME,
    "permanent": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "contractor": EmploymentType.CONTRACT,
    "freelance": EmploymentType.CONTRACT,
    "internship": EmploymentType.INTERNSHIP,
    "intern": EmploymentType.INTERNSHIP,
    "temporary": EmploymentType.TEMPORARY,
    "temp": EmploymentType.TEMPORARY,
}

REMOTE_ALIASES: dict[str, RemoteType] = {
    "remote": RemoteType.REMOTE,
    "fully remote": RemoteType.REMOTE,
    "wfh": RemoteType.REMOTE,
    "work from home": RemoteType.REMOTE,
    "hybrid": RemoteType.HYBRID,
    "onsite": RemoteType.ONSITE,
    "on-site": RemoteType.ONSITE,
    "on site": RemoteType.ONSITE,
    "in office": RemoteType.ONSITE,
    "in-office": RemoteType.ONSITE,
}

EDUCATION_ALIASES: dict[str, EducationLevel] = {
    "none": EducationLevel.NONE,
    "diploma": EducationLevel.DIPLOMA,
    "bachelor": EducationLevel.BACHELORS,
    "bachelors": EducationLevel.BACHELORS,
    "bachelor's": EducationLevel.BACHELORS,
    "be": EducationLevel.BACHELORS,
    "b.e.": EducationLevel.BACHELORS,
    "btech": EducationLevel.BACHELORS,
    "b.tech": EducationLevel.BACHELORS,
    "bs": EducationLevel.BACHELORS,
    "bsc": EducationLevel.BACHELORS,
    "undergraduate": EducationLevel.BACHELORS,
    "master": EducationLevel.MASTERS,
    "masters": EducationLevel.MASTERS,
    "master's": EducationLevel.MASTERS,
    "mtech": EducationLevel.MASTERS,
    "m.tech": EducationLevel.MASTERS,
    "ms": EducationLevel.MASTERS,
    "msc": EducationLevel.MASTERS,
    "mba": EducationLevel.MASTERS,
    "phd": EducationLevel.PHD,
    "ph.d.": EducationLevel.PHD,
    "doctorate": EducationLevel.PHD,
}

SALARY_PERIOD_ALIASES: dict[str, SalaryPeriod] = {
    "yearly": SalaryPeriod.YEARLY,
    "year": SalaryPeriod.YEARLY,
    "annual": SalaryPeriod.YEARLY,
    "annually": SalaryPeriod.YEARLY,
    "per annum": SalaryPeriod.YEARLY,
    "pa": SalaryPeriod.YEARLY,
    "monthly": SalaryPeriod.MONTHLY,
    "month": SalaryPeriod.MONTHLY,
    "per month": SalaryPeriod.MONTHLY,
    "hourly": SalaryPeriod.HOURLY,
    "hour": SalaryPeriod.HOURLY,
    "per hour": SalaryPeriod.HOURLY,
}


def _map(value: str | None, aliases: dict[str, _E], default: _E) -> _E:
    if not value:
        return default
    return aliases.get(value.strip().lower(), default)


def normalize_employment_type(value: str | None) -> EmploymentType:
    return _map(value, EMPLOYMENT_TYPE_ALIASES, EmploymentType.UNKNOWN)


def normalize_remote(value: str | None) -> RemoteType:
    return _map(value, REMOTE_ALIASES, RemoteType.UNKNOWN)


def normalize_education(value: str | None) -> EducationLevel:
    return _map(value, EDUCATION_ALIASES, EducationLevel.UNKNOWN)


def normalize_salary_period(value: str | None) -> SalaryPeriod:
    return _map(value, SALARY_PERIOD_ALIASES, SalaryPeriod.UNKNOWN)
