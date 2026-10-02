# Compliance and Scaling Roadmap

While the foundational event-driven architecture of the AI Intelligence Platform is highly modular and functional, transitioning to an enterprise-grade, production-ready system requires addressing specific gaps in compliance, security, and scalability.

This document outlines the known gaps and proposed architectural solutions.

---

## 🛡️ 1. Compliance & Security Gaps

### A. Secret Sanitization (SOC2/ISO27001)
* **The Gap:** The platform extracts raw source code based on the AST blast radius and sends it directly to cloud LLMs (OpenAI/Gemini). If a developer accidentally commits a secret (e.g., AWS key, password), it is transmitted to a 3rd-party AI provider.
* **The Fix:** Implement a regex-based secret scrubber (such as integrating *TruffleHog* or *Gitleaks* as a library) as a middleware step right before `LlmService.analyze_ast()`. If secrets are detected, they should be masked (e.g., `REDACTED_SECRET`) before hitting the LLM.

### B. Encryption at Rest for Credentials
* **The Gap:** GitHub Personal Access Tokens (PATs) and LLM API Keys (OpenAI/Gemini) are currently stored in plain text in the PostgreSQL database (`scm_accounts` and `platform_settings` tables).
* **The Fix:** Implement Application-Level Encryption. Utilize a Key Management Service (KMS) or a library like Python's `cryptography` (Fernet) to encrypt these tokens prior to saving them to the database, and decrypt them strictly in-memory during execution.

### C. Data Residency & LLM Zero-Retention
* **The Gap:** Enterprise compliance standards often dictate strict data residency and retention policies for proprietary source code.
* **The Fix:** 
  1. Ensure that API calls to OpenAI/Gemini explicitly use organizational endpoints that guarantee zero-day retention (no training on user data).
  2. Implement a project-level setting to force "Local-Only Inference" (e.g., routing exclusively to Ollama) for repositories flagged as highly sensitive.

---

## 📈 2. Scaling & Resilience Gaps

### A. Distributed Message Broker (Job Queueing)
* **The Gap:** The platform currently relies on `job_poller.py`, which executes a `while True:` loop checking PostgreSQL for pending jobs. In high-traffic scenarios (e.g., dozens of PRs opened concurrently), this database-polling mechanism will bottleneck, and long-running AST parsing will block the queue.
* **The Fix:** Replace the database-polling mechanism with a robust distributed task queue, such as **Celery backed by Redis or RabbitMQ**. This will enable scaling out to multiple concurrent background worker nodes dynamically.

### B. Context Window Chunking
* **The Gap:** For massive Pull Requests, the 1-hop AST traversal may extract context that exceeds a model's maximum context window (e.g., > 128k tokens). Currently, this will result in a hard API failure (MaxTokens exceeded).
* **The Fix:** Implement a "Map-Reduce" review strategy. If the generated prompt payload exceeds the maximum token limit, the orchestrator should split the AST into logical sub-components, evaluate them via parallel LLM calls, and utilize a final synthesis LLM call to aggregate the findings.

### C. API Rate Limiting & Backoff
* **The Gap:** GitHub enforces strict API rate limits, and Cloud LLM providers enforce tokens-per-minute (TPM) and requests-per-minute (RPM) limits. Aggressive polling and commenting on large PRs can result in HTTP 429 (Too Many Requests) blocks.
* **The Fix:** Introduce standard exponential backoff and retry mechanisms (using a library like `tenacity`) around all external network boundaries, explicitly handling 429 and 502 HTTP status codes.

### D. Git Clone Optimization (Disk I/O)
* **The Gap:** The `WorkspaceManager` executes a full `git clone` for every webhook trigger. For massive monorepos, this can take several minutes and consume significant Disk I/O.
* **The Fix:** 
  1. Default to Shallow Clones (`git clone --depth 1`) where deep git history is not strictly required.
  2. For high-volume repositories, maintain a persistent "bare" repository cache on the worker nodes that only requires a delta `git fetch`, cloning locally from the bare cache to drastically reduce network and I/O latency.
