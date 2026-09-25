# Distributed Job Scraper & Matcher Bot

## Generate and store job embeddings

The embedding pipeline uses local FastEmbed (`sentence-transformers/all-MiniLM-L6-v2`,
384 dimensions) and PostgreSQL with the **pgvector** extension. Install pgvector
on the PostgreSQL server first: https://github.com/pgvector/pgvector#installation.
The database user must be allowed to run `CREATE EXTENSION IF NOT EXISTS vector`.
Installing a Python package alone does not install the PostgreSQL extension.

From the project root in PowerShell:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python embed_jobs.py --limit 50
```

Uses `DB_HOST`, `DB_PORT` (default 5432), `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
and `GROQ_API_KEY` from `backend/.env`. Install `requirements.txt` if needed.
The first run downloads the embedding model. Structured job extraction calls
Groq; embedding generation then runs locally.

The command copies existing `jobs` into `raw_jobs` by unique application link,
processes up to the requested number of pending rows, and stores structured
fields and vectors in `processed_jobs.embedding`. Repeated runs skip completed
jobs. Use `python embed_jobs.py --limit 50 --retry-failed` to retry failures.
Run one embedding command at a time; it is a batch worker, not a concurrent queue.
Run it again after scraping to embed newly saved jobs. This backfill includes
only jobs retained by the existing scraper/scorer, plus any pending raw jobs.

Verify in PostgreSQL:

```sql
SELECT id, role, vector_dims(embedding) AS dimensions
FROM processed_jobs LIMIT 10;
```

Model and embedding recipe must remain consistent when embedding candidate
profiles for future similarity search. Changing the model requires re-embedding
stored jobs. Resume upload and vector search are not yet connected to the UI.

An intelligent, distributed job scraping and filtering pipeline. The bot scrapes job openings from LinkedIn, filters out irrelevant positions using a fast deterministic pre-filter, passes potential matches into a RabbitMQ message queue, and evaluates them using a background AI matching worker powered by the Google Gemini API.

---

## 🏗️ Architecture & Flow

The project is structured as a decoupled **Producer-Consumer** architecture using **RabbitMQ**:

```mermaid
graph TD
    A[LinkedIn Scraper] -->|New Job Found| B(Deterministic Scorer)
    B -->|REJECTED| C[Drop Job]
    B -->|MATCH| D[Publish to RabbitMQ jobs_queue]
    D --> E[RabbitMQ Broker]
    E -->|Distribute Message| F[AI Worker Consumer Thread]
    F --> G(Gemini AI Scorer)
    G -->|Strong/Partial Match| H[Log / Save to DB]
    G -->|Poor Match / Low Score| I[Drop Job]
```

1. **Producer (LinkedIn Scraper)**: Scrapes jobs using browser automation.
2. **Fast Pre-Filter**: Runs a fast, free local regex filter to knock out forbidden terms (e.g., `Senior`, `Lead`, `Manager`).
3. **Message Queue (RabbitMQ)**: Stores valid pre-filtered jobs, making the system scalable and decoupled.
4. **Consumer (AI Worker)**: Listens to the RabbitMQ queue in a background thread, calling the Gemini API to deep-analyze job descriptions against the candidate's profile.

---

## 📁 Project Structure

* **`main.py`**: The main entrypoint. Starts the background AI Worker thread and kicks off the scraper on the main thread.
* **`Queue/job_queue.py`**: Handles RabbitMQ connection setup, the scraping pipeline callback (Producer), and the background AI worker (Consumer).
* **`scraper/`**: Contains the LinkedIn scraper logic (`linkedin_bot.py`).
* **`scorer/`**:
  * `deterministic_job_scrorer.py`: Contains regex filtering logic to knock out senior/unrelated titles.
  * `ai_scorer.py`: Interfaces with the Google Gemini API to grade matching jobs against the target developer profile.
* **`db/`**: Workspace for database configurations and SQLAlchemy models to store successful matches.

---

## 🚀 Setup Instructions

### 1. Prerequisites
Ensure you have:
* Python 3.10+
* **RabbitMQ** (Running locally. The easiest way is using Docker: `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`)

### 2. Installation
Clone the repository, set up a virtual environment, and install dependencies:

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install pika google-generativeai python-dotenv linkedin-jobs-scraper sqlalchemy psycopg2-binary
```

### 3. Environment Configuration
Create a `.env` file in the project root:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///jobs.db  # Or postgresql://user:pass@localhost:5432/dbname
```

---

## 🏃 How to Run

1. **Start RabbitMQ**:
   Make sure RabbitMQ is running on `localhost:5672`.

2. **Run the Application**:
   Start the pipeline by running:
   ```bash
   python main.py
   ```

This starts the background AI consumer worker, spins up Chrome, and starts scraping jobs. Matches and drops will be logged in real-time.
