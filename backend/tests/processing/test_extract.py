import json

import pytest

from processing.schemas import ExtractedJob
from processing.stages.extract import (
    ExtractionError,
    JobExtractor,
    build_prompt,
    parse_extracted,
)


# --- a fake Groq client: mimics client.chat.completions.create(...).choices[0].message.content
class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class _Resp:
    def __init__(self, content):
        self.choices = [_Msg(content)]


class _Completions:
    def __init__(self, content=None, error=None):
        self._content, self._error = content, error
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self._error:
            raise self._error
        return _Resp(self._content)


def _fake_client(content=None, error=None):
    completions = _Completions(content=content, error=error)
    client = type("C", (), {})()
    client.chat = type("Chat", (), {"completions": completions})()
    return client, completions


VALID_JSON = json.dumps(
    {
        "role": "Backend Engineer",
        "seniority": "Junior",
        "skills": ["NodeJS", "PostgreSQL"],
        "nice_to_have_skills": ["Docker"],
        "experience_min_years": 1,
        "experience_max_years": None,
        "salary": {"min_amount": 1000000, "max_amount": 1800000, "currency": "INR", "period": "yearly"},
        "location": "Bengaluru",
        "remote": "hybrid",
        "employment_type": "full time",
        "education": "bachelors",
        "domain": "fintech",
        "responsibilities": ["Build APIs"],
    }
)


# --- build_prompt (pure) --------------------------------------------------- #
def test_build_prompt_includes_title_and_description():
    p = build_prompt("Backend Engineer", "We use Node.js")
    assert "Backend Engineer" in p and "We use Node.js" in p


def test_build_prompt_states_the_company_history_rule():
    p = build_prompt("x", "y").lower()
    assert "founded in" in p and "candidate" in p


# --- parse_extracted (pure) ------------------------------------------------ #
def test_parse_valid_json_preserves_raw_values():
    job = parse_extracted(VALID_JSON)
    assert isinstance(job, ExtractedJob)
    assert job.seniority == "Junior"          # not normalized here
    assert job.skills == ["NodeJS", "PostgreSQL"]
    assert job.salary.period == "yearly"       # permissive string, no enum


def test_parse_empty_raises():
    with pytest.raises(ExtractionError):
        parse_extracted("")


def test_parse_malformed_json_raises():
    with pytest.raises(ExtractionError):
        parse_extracted("{not valid json")


def test_parse_schema_mismatch_raises():
    with pytest.raises(ExtractionError):
        parse_extracted('{"experience_min_years": "not-a-number"}')


# --- JobExtractor.extract (I/O, faked client) ------------------------------ #
def test_extract_returns_parsed_job():
    client, _ = _fake_client(content=VALID_JSON)
    job = JobExtractor(client=client).extract("Backend Engineer", "desc")
    assert job.role == "Backend Engineer"


def test_extract_retries_then_raises(monkeypatch):
    monkeypatch.setattr("processing.stages.extract.time.sleep", lambda *_: None)
    client, completions = _fake_client(error=RuntimeError("rate limit"))
    with pytest.raises(ExtractionError):
        JobExtractor(client=client).extract("x", "y", max_retries=3, base_delay=0)
    assert completions.calls == 3   # retried the configured number of times
