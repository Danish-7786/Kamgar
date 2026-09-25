# Collect Greenhouse and Ashby jobs

From the repository root in PowerShell:

```powershell
.\backend\venv\Scripts\python.exe backend\collect_ats_jobs.py
```

The command reads `backend/utils/company.json` and writes `backend/ats_jobs.json`
with two keys: `jobs` (normalized records) and `reports` (one result per company).
The output file is replaced on each run. These are all jobs on the configured
boards, before title/location filtering. This command does not insert into the
database or publish to RabbitMQ.

Add companies as objects in the JSON list:

```json
{"name": "Company name", "source": "greenhouse", "board": "company-token"}
```

Use `greenhouse` or `ashby` for `source`. Use the token in the actual careers URL,
not a guessed company name or the whole URL. For example:

- `https://job-boards.greenhouse.io/stripe` -> `stripe`
- `https://jobs.ashbyhq.com/Ashby` -> `Ashby` (preserve case)

Stripe and Ashby are starter companies. Replace or extend them as needed.
The default registry path is resolved from the Python file, so it works when
running from either the project root or the backend directory.

Use a different registry or output destination:

```powershell
.\backend\venv\Scripts\python.exe backend\collect_ats_jobs.py --companies backend\utils\company.json --output backend\ats_jobs.json
```

## How it works

1. `load_companies()` reads the JSON list.
2. `collect_companies()` validates each entry and selects its collector.
3. The shared HTTP client uses 5-second connection and 30-second read timeouts,
   with up to three retries for eligible failures and backoff between retries.
   It respects `Retry-After` for rate limiting. These timeouts are not a total
   run deadline; response-body download failures are reported, not always retried.
4. Each collector maps the provider response into the same job dictionary.
5. Failed companies get a report with an error; other companies continue.

Malformed company entries and malformed job records are reported as company
failures. A company's jobs are retained only when its whole batch maps
successfully. An empty successful board has `status: success` and `job_count: 0`.
A failed board has `status: failed`. The command saves successful companies even
when others fail, then exits with code 1 if any company failed.

Greenhouse descriptions are converted from HTML to text. Its update timestamp
is not used as the posting date. Ashby unlisted jobs are skipped; its posting
date is the date of last publication. Original provider fields, including
additional locations and compensation, remain in `raw_payload`.

For use in backend Python code:

```python
from scraper.ats_collectors import collect_companies

jobs, reports = collect_companies()  # reads the default company registry
```

API references:
- https://docs.greenhouse.io/job-board.html
- https://developers.ashbyhq.com/docs/public-job-posting-api
