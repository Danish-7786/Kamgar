"""Seniority normalization: free text -> Seniority enum.

"Junior", "Graduate", "Trainee" all fold to Entry. Unknown -> UNKNOWN.
"""

from __future__ import annotations

from processing.schemas import Seniority

SENIORITY_ALIASES: dict[str, Seniority] = {
    "junior": Seniority.ENTRY,
    "jr": Seniority.ENTRY,
    "graduate": Seniority.ENTRY,
    "grad": Seniority.ENTRY,
    "trainee": Seniority.ENTRY,
    "fresher": Seniority.ENTRY,
    "entry": Seniority.ENTRY,
    "entry level": Seniority.ENTRY,
    "entry-level": Seniority.ENTRY,
    "associate": Seniority.ENTRY,
    "intern": Seniority.ENTRY,
    "mid": Seniority.MID,
    "mid level": Seniority.MID,
    "mid-level": Seniority.MID,
    "intermediate": Seniority.MID,
    "senior": Seniority.SENIOR,
    "sr": Seniority.SENIOR,
    "lead": Seniority.LEAD,
    "team lead": Seniority.LEAD,
    "tech lead": Seniority.LEAD,
    "staff": Seniority.LEAD,
    "principal": Seniority.PRINCIPAL,
    "architect": Seniority.PRINCIPAL,
}


def normalize_seniority(value: str | None) -> Seniority:
    if not value:
        return Seniority.UNKNOWN
    return SENIORITY_ALIASES.get(value.strip().lower(), Seniority.UNKNOWN)
