"""Module 3: AI extraction.

Turns a cleaned job description into a structured ``ExtractedJob`` using an
LLM (Groq, JSON mode). Design split:

  * ``build_prompt`` / ``parse_extracted`` are PURE — no network, unit-tested
    directly.
  * ``JobExtractor._complete`` is the only I/O. The Groq client is injected,
    so tests pass a fake client and never touch the network.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional

from pydantic import ValidationError

from processing.schemas import ExtractedJob


class ExtractionError(Exception):
    """Raised when the LLM output cannot be parsed into an ExtractedJob."""


_SYSTEM_PROMPT = (
    "You are a precise information-extraction engine for job postings. "
    "You output ONLY valid JSON matching the requested schema. You never "
    "invent facts: if a field is not stated, use null (or [] for lists)."
)


def build_prompt(title: str, description: str) -> str:
    """Pure. Build the extraction prompt. The experience rule lives here —
    it is the primary defense against counting company history as candidate
    experience (validation in Module 4 is the backstop)."""
    return f"""Extract structured data from this job posting.

Job Title: {title}

Job Description:
{description}

RULES:
- experience_min_years / experience_max_years refer ONLY to the work
  experience the CANDIDATE is required to have. NEVER use the company's age,
  how long the company has existed, "founded in", "N years in business", or a
  product's age. If a single figure is given ("3+ years"), set min to it and
  leave max null.
- Extract skills as concrete technologies/tools. Do NOT fix spelling or
  casing (leave "NodeJS" as "NodeJS") — normalization happens later.
- responsibilities: a short list of what the person will actually do.
- If a field is not present, use null (or [] for lists). Do not guess.

Return ONLY a JSON object with EXACTLY these keys:
{{
  "role": string|null,
  "seniority": string|null,
  "skills": string[],
  "nice_to_have_skills": string[],
  "experience_min_years": integer|null,
  "experience_max_years": integer|null,
  "salary": {{"min_amount": number|null, "max_amount": number|null, "currency": string|null, "period": string|null}}|null,
  "location": string|null,
  "remote": string|null,
  "employment_type": string|null,
  "education": string|null,
  "domain": string|null,
  "responsibilities": string[]
}}"""


def parse_extracted(raw_json: Optional[str]) -> ExtractedJob:
    """Pure. JSON text -> validated ExtractedJob. Raises ExtractionError on
    malformed JSON or schema mismatch."""
    if not raw_json:
        raise ExtractionError("LLM returned empty content")
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise ExtractionError(f"LLM did not return valid JSON: {e}") from e
    try:
        return ExtractedJob.model_validate(data)
    except ValidationError as e:
        raise ExtractionError(f"JSON did not match ExtractedJob schema: {e}") from e


class JobExtractor:
    def __init__(self, client=None, model: str = "openai/gpt-oss-120b"):
        # Client is injectable so tests supply a fake; in production we build
        # the real Groq client lazily from the environment.
        if client is None:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY is missing from the environment")
            client = Groq(api_key=api_key)
        self.client = client
        self.model = model

    def _complete(self, prompt: str) -> str:
        """The only I/O in this module."""
        resp = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=0.0,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content

    def extract(
        self, title: str, description: str, *, max_retries: int = 4, base_delay: float = 2.0
    ) -> ExtractedJob:
        """Extract with bounded retries. Transient failures (rate limit,
        network) are retried; a persistent one raises ExtractionError so the
        orchestrator can quarantine the job rather than crash the batch."""
        prompt = build_prompt(title, description)
        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return parse_extracted(self._complete(prompt))
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (attempt + 1))
        raise ExtractionError(
            f"Extraction failed after {max_retries} attempts: {last_err}"
        )
