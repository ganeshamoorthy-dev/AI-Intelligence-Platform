# AI Intelligence Platform

An event-driven, privacy-first AI Code Review platform. It performs deep, context-aware structural analysis of Pull Requests by generating Abstract Syntax Trees (AST) and analyzing the architectural blast radius of code changes using multi-model Large Language Models (LLMs).

---

## 🏗️ High-Level Architecture

The platform operates on an **event-driven architecture**. When a developer opens a Pull Request, GitHub fires a webhook to the FastAPI backend. The orchestrator spawns an asynchronous background worker that clones the repository into an ephemeral workspace, parses the raw `git diff`, maps the changes to a structural AST subgraph, and feeds that highly targeted context to an LLM. Finally, the LLM's findings are published directly back to GitHub as inline review comments.

### Tech Stack

**Backend (Python)**
* **FastAPI**: High-performance asynchronous API framework.
* **SQLAlchemy (Async)**: ORM for PostgreSQL interactions.
* **Alembic**: Database schema migrations.
* **LangChain**: LLM orchestration and dynamic prompt formatting.
* **Uvicorn & asyncio**: ASGI server and background task execution.

**Frontend (Angular)**
* **Angular 17+**: Standalone components and reactive Signals.
* **Angular Material**: Modern, accessible UI components.
* **RxJS**: Asynchronous data streams and HTTP interception.

**AI / LLM Providers**
* **Ollama**: Local, privacy-first inference (e.g., Qwen 2.5, Llama 3).
* **OpenAI & Google Gemini**: Cloud-based powerful inference.

---

## 🔄 Core Pipeline Flow

When a webhook is received (or a review is triggered manually via the UI), the background `JobPoller` initiates the `ReviewService.execute_review()` pipeline:

1. **Ephemeral Workspace**: The specific PR branch is cloned into a temporary filesystem directory.
2. **Diff Parsing**: `ChangedSymbolService` parses the raw `git diff` to identify exactly which files and line numbers were added or modified.
3. **AST Generation**: `GraphifyService` parses the codebase into an Abstract Syntax Tree.
4. **Blast Radius Calculation**: `GraphTraversalService` maps the modified lines to specific AST nodes (functions/classes) and extracts a "1-hop" structural dependency subgraph.
5. **Context Extraction**: `SourceContextService` extracts the raw source code string for only the affected nodes.
6. **LLM Inference**: The extracted context, AST subgraph, and diff are fed into `LlmService`, which prompts the LLM to identify security flaws and architectural risks based on global severity heuristics.
7. **Publishing**: `GithubPublisherService` maps the LLM findings back to the original git diff and posts them as inline PR comments. If a line number falls outside the diff, it gracefully falls back to a general markdown table comment.

---

## 🗄️ Database Schema

* **PlatformSettings**: A single-row table containing global configurations (Default LLM model, Severity Thresholds, API Keys, Custom Instructions).
* **ScmAccount**: Registered GitHub/GitLab accounts with Personal Access Tokens.
* **Project**: Represents a specific Git repository.
* **PullRequest**: Represents a specific PR within a Project.
* **ReviewRun**: Tracks the lifecycle, latency, input/output tokens, and status (`pending`, `completed`, `failed`) of a single AI review execution.
* **ReviewFinding**: Granular bugs or vulnerabilities identified by the LLM, linked to a specific `ReviewRun`.
* **ScmWebhook**: Stores the GitHub webhook configuration and dynamically overrides the LLM model for specific webhooks.

---

## 🎨 User Interface (Dashboard)

The Angular frontend provides a clean control plane for the system:
* **Jobs**: Real-time view of review executions, token usage, and latencies.
* **Integrations**: Tabbed interface to manage SCM accounts and configure new repository webhooks.
* **Review Report**: Deep dive into a specific `ReviewRun`, showcasing the Blast Radius summary, the AST Impact Graph, and the tabulated findings.
* **Settings**: Configure global heuristics, minimum severity thresholds, custom LLM instructions, and manage API keys.

---

## 🚀 Setup & Execution

### Backend
\`\`\`bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt

# Run migrations to build the schema
python -m alembic upgrade head

# Start the FastAPI Server
uvicorn app.main:app --reload

# Start the Background Worker (in a separate terminal)
python -m app.workers.job_poller
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
npm start
\`\`\`
