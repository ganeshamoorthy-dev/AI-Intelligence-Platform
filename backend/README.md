# AI Developer Intelligence Platform — Backend

A **privacy-first, event-driven** backend that performs intelligent, context-aware code reviews on GitHub Pull Requests using a local LLM (Ollama) and an Abstract Syntax Tree (AST) pipeline.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Review Pipeline](#review-pipeline)

---

## Overview

When a Pull Request is **opened** or **updated** on GitHub, the backend:

1. Receives the event via a **GitHub Webhook**
2. Queues a background **ReviewRun** job
3. Clones an ephemeral workspace of the repository
4. Parses the codebase into an **AST graph** using `graphify`
5. Extracts the **diff** (changed files, lines, and symbols)
6. Computes a **Blast Radius** (which other parts of the codebase are impacted)
7. Sends all context to a **local LLM** (Ollama / qwen2.5-coder) for analysis
8. Saves the **findings** to PostgreSQL and publishes a review comment back to GitHub

---

## Architecture

The backend follows a strict **Clean Architecture** (layered architecture).

```
HTTP Request / Webhook
        │
        ▼
  ┌─────────────┐
  │   API Layer │  (app/api/) — FastAPI Routers
  └──────┬──────┘
         │ calls
         ▼
  ┌─────────────┐
  │  Service    │  (app/services/) — Business Logic
  │  Layer      │
  └──────┬──────┘
         │ reads/writes
         ▼
  ┌─────────────┐
  │  Repository │  (app/repositories/) — Data Access
  │  Layer      │
  └──────┬──────┘
         │ uses
         ▼
  ┌─────────────┐
  │  DB Models  │  (app/db/models.py) — SQLAlchemy Entities
  └─────────────┘
```

### Spring Boot Analogy

| Concept | Spring Boot | FastAPI Equivalent |
|:---|:---|:---|
| Framework | Spring Boot (Tomcat) | FastAPI (Uvicorn, Async) |
| Controllers | `@RestController` | `APIRouter()` |
| Dependency Injection | `@Autowired` | `Depends()` |
| DTOs / Validation | `@Valid`, Jackson | Pydantic `BaseModel` |
| ORM | Hibernate / JPA | SQLAlchemy 2.0 |
| Entities | `@Entity`, `@Column` | `DeclarativeBase`, `mapped_column` |
| Repositories | `JpaRepository<T, ID>` | `BaseRepository` (custom generic) |
| Database Migrations | Flyway / Liquibase | Alembic |
| Background Tasks | `@Scheduled`, Quartz | `asyncio` polling loop |

---

## Tech Stack

| Technology | Purpose |
|:---|:---|
| **FastAPI** | Async HTTP framework and API layer |
| **Uvicorn** | ASGI server |
| **PostgreSQL** | Primary relational database |
| **SQLAlchemy 2.0** | Async ORM (with `asyncpg` driver) |
| **Alembic** | Database schema migrations |
| **Pydantic v2** | Request/response validation and settings |
| **LangChain + Ollama** | LLM inference (`qwen2.5-coder:7b` by default) |
| **graphify** | AST & dependency graph generation for Python/JS codebases |
| **httpx** | Async HTTP client (for GitHub API calls) |
| **pytest** | Test runner |

---

## Directory Structure

```
Backend/
├── app/
│   ├── api/                    # HTTP Controllers (FastAPI Routers)
│   │   ├── dashboard.py        # Metrics and job listing
│   │   ├── github.py           # GitHub repo & PR listing
│   │   ├── ide.py              # IDE integration endpoints
│   │   ├── reviews.py          # Manual review trigger
│   │   ├── scm_accounts.py     # SCM account management
│   │   ├── settings.py         # Platform settings (LLM keys, config)
│   │   └── webhooks.py         # GitHub Webhook receiver
│   ├── core/
│   │   ├── config.py           # App settings via pydantic-settings (.env)
│   │   └── security.py         # API key verification middleware
│   ├── db/
│   │   ├── models.py           # SQLAlchemy ORM entity definitions
│   │   └── session.py          # Async DB session factory
│   ├── repositories/
│   │   ├── base.py             # Generic BaseRepository<T>
│   │   └── job_repo.py         # ReviewRun-specific queries
│   ├── schemas/
│   │   └── webhooks.py         # Pydantic schemas for webhook payloads
│   ├── services/
│   │   ├── review/
│   │   │   └── orchestrator.py # Core AI review pipeline orchestrator
│   │   ├── change/             # Diff parsing and symbol change detection
│   │   ├── context/            # Context engine (Blast Radius builder)
│   │   ├── graph/              # AST graph traversal and source extraction
│   │   ├── graphify/           # graphify CLI wrapper (AST parsing)
│   │   ├── llm/                # LLM inference via LangChain + Ollama
│   │   ├── prompt/             # LLM prompt templates
│   │   ├── scm/                # SCM provider abstraction (GitHub, GitLab)
│   │   └── workspace/          # Ephemeral Git clone manager
│   ├── workers/
│   │   └── job_poller.py       # Background asyncio loop — polls pending jobs
│   └── main.py                 # Application entrypoint, router registration
├── alembic/                    # Database migration scripts
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
├── init_db.py                  # One-time DB initializer script
└── .env                        # Environment variables (not committed)
```

---

## Database Models

| Model | Table | Description |
|:---|:---|:---|
| `PlatformSettings` | `platform_settings` | Global LLM API keys, severity threshold, custom instructions |
| `ScmAccount` | `scm_accounts` | GitHub/GitLab/Bitbucket OAuth tokens |
| `ScmWebhook` | `scm_webhooks` | Per-project webhook registration and LLM model override |
| `Project` | `projects` | Registered repositories with review policies |
| `PullRequest` | `pull_requests` | Tracked pull requests per project |
| `ReviewRun` | `review_runs` | A single AI review job (pending → processing → completed) |
| `ReviewFinding` | `review_findings` | Individual issues found by the LLM (file, line, severity, category) |

---

## API Endpoints

All endpoints (except webhooks) require an API key via the `X-API-Key` header.

| Method | Path | Description |
|:---|:---|:---|
| `GET` | `/api/v1/health` | Health check (DB + LLM connectivity) |
| `GET` | `/api/v1/dashboard/metrics` | Aggregated platform metrics |
| `GET` | `/api/v1/dashboard/jobs` | Recent review job list |
| `GET` | `/api/v1/dashboard/jobs/{id}/findings` | Findings for a specific job |
| `POST` | `/api/v1/reviews/trigger` | Manually trigger a PR review by URL |
| `POST` | `/api/v1/webhooks/github` | GitHub webhook receiver (HMAC-verified) |
| `GET` | `/api/v1/github/repos` | List GitHub repositories for a linked account |
| `GET` | `/api/v1/github/repos/{owner}/{repo}/pulls` | List open PRs for a repository |
| `GET` | `/api/v1/scm-accounts` | List linked SCM accounts |
| `POST` | `/api/v1/scm-accounts` | Add a new SCM account |
| `DELETE` | `/api/v1/scm-accounts/{id}` | Remove an SCM account |
| `GET` | `/api/v1/settings` | Get platform settings |
| `PUT` | `/api/v1/settings` | Update platform settings |
| `GET` | `/api/v1/ide/review` | IDE integration — sync review endpoint |

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Environment Variables

Create a `.env` file in the `Backend/` directory:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_platform

# GitHub Webhook
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret

# LLM (Ollama running locally)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5-coder:7b

# Optional — Cloud LLM (overrides Ollama if set)
OPENAI_API_KEY=
GOOGLE_API_KEY=

# File System
GRAPHIFY_CLI_PATH=graphify
WORKSPACE_BASE_DIR=D:\workspace\AI Intelligence Platform\tempclonedir
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- [Ollama](https://ollama.com/) running locally with `qwen2.5-coder:7b` pulled
- [graphify](https://pypi.org/project/graphifyy/) CLI installed

### 1. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example variables above into a `.env` file inside `Backend/`.

### 4. Initialize the Database

```bash
# Run migrations
alembic upgrade head

# (Optional) Seed initial data
python init_db.py
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload
```

The server starts at **http://localhost:8000**.

---

## Database Migrations

Alembic is used for schema migrations — equivalent to Flyway/Liquibase in Spring Boot.

```bash
# Generate a new migration after changing models.py
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

---

## Testing

```bash
pytest
```

Additional test scripts for development:

```bash
# Test AST extraction on a local repo
python test_extraction_simple.py

# Test source context extraction
python test_source_context.py
```

---

## Review Pipeline

The core AI review pipeline is orchestrated by [`ReviewService`](app/services/review/orchestrator.py):

```
1. Clone repo into ephemeral temp directory
        │
        ▼
2. Parse codebase AST with graphify
        │
        ▼
3. Fetch PR diff from GitHub API
        │
        ▼
4. Identify changed symbols via ChangeAnalyzer
        │
        ▼
5. Compute Blast Radius (graph traversal — depth-1, bidirectional)
        │
        ▼
6. Extract source code snippets for context
        │
        ▼
7. Build structured LLM context (ContextEngine)
        │
        ▼
8. Run LLM inference (LangChain → Ollama / OpenAI / Gemini)
        │
        ▼
9. Persist findings to PostgreSQL
        │
        ▼
10. Publish review comment back to GitHub PR
```

---

### Simulate a Webhook (Local Testing)

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "x-github-event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "number": 1,
      "title": "Test PR",
      "user": {"login": "testuser"},
      "head": {"sha": "abcdef123456"},
      "base": {"sha": "123456abcdef"}
    },
    "repository": {
      "full_name": "testuser/test-repo",
      "clone_url": "https://github.com/testuser/test-repo.git"
    }
  }'
```

> **Note:** If the project has a `webhook_secret` configured, the request must include a valid `x-hub-signature-256` header. For local testing, you can temporarily disable HMAC verification in [`webhooks.py`](app/api/webhooks.py).
