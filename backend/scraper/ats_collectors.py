import json
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from utils.httpClient import create_session, fetch_jobs


DEFAULT_COMPANIES_FILE = Path(__file__).resolve().parents[1] / "utils" / "company.json"


def load_companies(path=DEFAULT_COMPANIES_FILE):
    """Read the company registry; individual entries are checked during collection."""
    with Path(path).open(encoding="utf-8-sig") as file:
        companies = json.load(file)
    if not isinstance(companies, list):
        raise ValueError("Company file must contain a JSON list of company objects")
    return companies


def validate_company(company):
    if not isinstance(company, dict):
        raise ValueError("Each company must be a JSON object")
    for field in ("name", "source", "board"):
        if not isinstance(company.get(field), str) or not company[field].strip():
            raise ValueError(f"Company requires a non-empty '{field}' string")
    company = {key: value.strip() for key, value in company.items()
               if key in ("name", "source", "board")}
    company["source"] = company["source"].lower()
    if company["source"] not in ("greenhouse", "ashby"):
        raise ValueError(f"Unsupported source: {company['source']}")
    if any(char in company["board"] for char in "/?#"):
        raise ValueError("Use the board token/name, not the full careers URL")
    return company


def required_text(posting, field):
    value = posting.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Job requires a non-empty '{field}' string")
    return value.strip()

def html_to_text(value):
    value = unescape(unescape(value or ""))
    return BeautifulSoup(value, "html.parser").get_text(separator="\n", strip = True)



def collect_greenhouse(session, company):
    board = quote(company["board"], safe="")
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"

    postings = fetch_jobs(session, url, params={"content": "true"})

    jobs = []

    for posting in postings:
        jobs.append({
            "source": "greenhouse",
            "external_id": str(posting["id"]),
            "title": required_text(posting, "title"),
            "company": company["name"],
            "link": required_text(posting, "absolute_url"),
            "description": html_to_text(posting.get("content")),
            "location": (posting.get("location") or {}).get("name"),
            "date_posted": None,
            "raw_payload": posting,
        })

    return jobs


def collect_ashby(session, company):
    board = quote(company["board"], safe="")
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"

    postings = fetch_jobs(
        session,
        url,
        params={"includeCompensation": "true"},
    )

    jobs = []

    for posting in postings:
        if posting.get("isListed") is False:
            continue

        published_at = posting.get("publishedAt")
        link = required_text(posting, "jobUrl")

        jobs.append({
            "source": "ashby",
            # Fall back to the job URL if no ID is supplied.
            "external_id": str(posting.get("id") or link),
            "title": required_text(posting, "title"),
            "company": company["name"],
            "link": link,
            "description": (
                posting.get("descriptionPlain")
                or html_to_text(posting.get("descriptionHtml"))
            ),
            "location": posting.get("location"),
            "date_posted": (
                datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                .date().isoformat() if published_at else None
            ),
            "raw_payload": posting,
        })

    return jobs


def collect_companies(companies=None):
    """Collect configured boards, keeping each company's failure separate.

    A malformed posting fails that company's entire batch, so partial results
    cannot be mistaken for a complete board snapshot.
    """
    if companies is None:
        companies = load_companies()
    collectors = {
        "greenhouse": collect_greenhouse,
        "ashby": collect_ashby,
    }

    all_jobs = []
    reports = []

    with create_session() as session:
        for company in companies:
            info = company if isinstance(company, dict) else {}
            report = {
                "company": info.get("name"),
                "source": info.get("source"),
                "board": info.get("board"),
            }

            try:
                company = validate_company(company)
                collector = collectors[company["source"]]
                jobs = collector(session, company)
                all_jobs.extend(jobs)

                report.update({
                    "status": "success",
                    "job_count": len(jobs),
                    "error": None,
                })

            except (
                requests.RequestException,
                ValueError,
                KeyError,
                TypeError,
                AttributeError,
            ) as exc:
                report.update({
                    "status": "failed",
                    "job_count": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                })

            reports.append(report)

    return all_jobs, reports
