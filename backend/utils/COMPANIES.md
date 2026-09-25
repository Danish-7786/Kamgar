# Companies using Greenhouse and Ashby

Verified on 2026-09-26 with read-only requests to each company's public jobs API.
All 18 configured boards returned HTTP 200 and a non-empty jobs list. Ashby
counts exclude postings explicitly marked `isListed: false`. Counts change over
time and include all listed locations and job types, not only India or software
engineering roles. API availability does not verify every individual opening.

The collectors read `company.json` in this directory. Its `board` field is the
exact API identifier; preserve capitalization, especially `Ashby`.

| Company | Platform | Board identifier | Postings at verification | API checked |
| --- | --- | --- | ---: | --- |
| Airbnb | Greenhouse | `airbnb` | 157 | [Jobs](https://boards-api.greenhouse.io/v1/boards/airbnb/jobs) |
| Cloudflare | Greenhouse | `cloudflare` | 393 | [Jobs](https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs) |
| Coinbase | Greenhouse | `coinbase` | 208 | [Jobs](https://boards-api.greenhouse.io/v1/boards/coinbase/jobs) |
| Databricks | Greenhouse | `databricks` | 888 | [Jobs](https://boards-api.greenhouse.io/v1/boards/databricks/jobs) |
| Figma | Greenhouse | `figma` | 163 | [Jobs](https://boards-api.greenhouse.io/v1/boards/figma/jobs) |
| GitLab | Greenhouse | `gitlab` | 198 | [Jobs](https://boards-api.greenhouse.io/v1/boards/gitlab/jobs) |
| MongoDB | Greenhouse | `mongodb` | 396 | [Jobs](https://boards-api.greenhouse.io/v1/boards/mongodb/jobs) |
| Stripe | Greenhouse | `stripe` | 698 | [Jobs](https://boards-api.greenhouse.io/v1/boards/stripe/jobs) |
| Ashby | Ashby | `Ashby` | 65 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/Ashby) |
| Cursor | Ashby | `cursor` | 126 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/cursor) |
| ElevenLabs | Ashby | `elevenlabs` | 208 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/elevenlabs) |
| Linear | Ashby | `linear` | 30 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/linear) |
| Notion | Ashby | `notion` | 129 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/notion) |
| OpenAI | Ashby | `openai` | 832 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/openai) |
| Perplexity | Ashby | `perplexity` | 123 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/perplexity) |
| Ramp | Ashby | `ramp` | 159 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/ramp) |
| Replit | Ashby | `replit` | 73 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/replit) |
| Zapier | Ashby | `zapier` | 9 | [Jobs](https://api.ashbyhq.com/posting-api/job-board/zapier) |

Candidates left out: `hubspot` on Greenhouse and `deel` / `vercel` on Ashby
returned empty jobs lists. `postman`, `razorpay`, and `phonepe` on Greenhouse
returned HTTP 404. These results only describe the tested identifiers, not
whether those companies are hiring through another board or platform.

Your background scraper calls `collect_companies()` with this registry, so its
next ATS collection will include the expanded list. Verification only requested
public listings; it did not publish jobs to RabbitMQ or invoke AI processing.

Official API documentation:
- [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html)
- [Ashby Public Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api)
