"""Fetch configured company boards and save jobs plus per-company reports."""

import argparse
import json
from pathlib import Path

from scraper.ats_collectors import (
    DEFAULT_COMPANIES_FILE,
    collect_companies,
    load_companies,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companies", 
                        type=Path, 
                        default=DEFAULT_COMPANIES_FILE,
                        help="Company JSON file (defaults to backend/utils/company.json)")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent / "ats_jobs.json",
                        help="Output JSON path; an existing file is replaced")
    args = parser.parse_args(argv)

    try:
        companies = load_companies(args.companies)
    except (OSError, ValueError) as exc:
        parser.error(f"Cannot load companies: {exc}")

    jobs, reports = collect_companies(companies)
    try:
        args.output.write_text(
            json.dumps({"jobs": jobs, "reports": reports}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        parser.error(f"Cannot write output: {exc}")

    for report in reports:
        detail = report["error"] or f"{report['job_count']} jobs"
        print(f"[{report['status']}] {report['company']} ({report['source']}): {detail}")
    print(f"Saved {len(jobs)} jobs and {len(reports)} reports to {args.output}")
    return 1 if any(report["status"] == "failed" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
