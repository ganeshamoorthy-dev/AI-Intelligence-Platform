# Antigravity AI Intelligence Platform: Context Engine Architecture

## Overview
One of the most significant challenges in AI-driven Code Review is **Context Scoping**. Sending an entire repository to an LLM will breach token limits, increase latency, and cause the model to hallucinate or lose focus (the "Needle in a Haystack" problem). Conversely, sending *only* the git diff prevents the LLM from understanding how the changes impact the broader system.

Our Context Engine solves this by using a **Multi-Layered Structural Analysis Pipeline**. Instead of treating code as plain text, we treat it as a directed graph.

This document details the 5 layers of the Context Engine and how they progressively distill a raw repository into the perfect LLM prompt.

---

## Layer 1: The Graphify Parser (AST & Dependency Mapping)

**What it does:**
When a PR is opened, the engine clones the repository and runs `GraphifyService`. This service parses the raw source code into an Abstract Syntax Tree (AST) and outputs a queryable graph of nodes (Files, Classes, Methods) and edges (`calls`, `imports`, `inherits`).

**How it improves context:**
It allows the engine to understand the codebase semantically rather than textually. We no longer rely on brittle `grep` searches to find where a function is used; we simply query the graph edges.

**Example:**
Instead of knowing that `UserService.java` exists, the engine knows:
* `UserService` is a `Class`
* It has a method `createUser()`
* `createUser()` has a `calls` edge pointing to `UserRepository.save()`

---

## Layer 2: The Change Analyzer (Semantic Diffing)

**What it does:**
The `ChangeAnalyzer` takes the raw Git diff (e.g., `+ line 45 in User.java`) and cross-references it against the Graphify AST boundaries (`_start` and `_end` lines of nodes). 

**How it improves context:**
LLMs struggle to understand fragmented diffs. By cross-referencing the diff with the AST, the engine translates "Line 45 changed" into "The `isRootUser` method changed." The LLM is explicitly told *which semantic symbols* were modified, giving it immediate structural orientation.

**Example:**
* **Raw Diff:** `+ return true; // in LoginServiceImpl.java line 42`
* **Semantic Context:** "Symbol `isRootUser` (Method) in `LoginServiceImpl.java` was modified."

---

## Layer 3: Graph Traversal (The "Blast Radius")

**What it does:**
Using the `GraphTraversalService`, the engine takes the semantically modified symbols from Layer 2 and traverses the graph outwards (e.g., a 1-hop or 2-hop radius). It identifies:
1. **Direct Callers:** Methods that invoke the changed code.
2. **Direct Callees:** Methods that the changed code relies on.
3. **Related Tests:** Test suites explicitly linked to the modified classes.

**How it improves context:**
This is the core of the engine's intelligence. If a developer changes a DTO (Data Transfer Object), the diff only shows the DTO change. But the Graph Traversal automatically pulls the `Controller` and `Mapper` that rely on that DTO into the context window, allowing the LLM to catch integration bugs (like IDORs or missing fields) that span multiple files.

**Example:**
If `UserResponseDto.java` adds a `password` field:
* The Blast Radius identifies that `UserController.getUserById()` returns this DTO.
* Both files are flagged for the LLM, allowing it to catch the data leak.

---

## Layer 4: Source Context Extraction & Safety Limits

**What it does:**
The `SourceContextService` iterates over the nodes inside the Blast Radius and extracts their raw source code directly from the filesystem. It enforces strict safety limits (e.g., `max_total_lines = 10000`) to protect the LLM.

**How it improves context:**
By extracting only the methods within the Blast Radius, we maximize the signal-to-noise ratio. The LLM gets the exact code it needs to verify logic, without being overwhelmed by the 50,000 other lines of code in the repository. The hard limits ensure local models (like `Qwen2.5-Coder`) don't crash due to Out-Of-Memory (OOM) errors.

**Example:**
If `SecurityConfig.java` is in the Blast Radius, the engine extracts *only* the `SecurityConfig` class block, dynamically truncating it if it exceeds 500 lines, ensuring the LLM token window remains healthy.

---

## Layer 5: The Context Serializer (Markdown Formatting)

**What it does:**
The `ContextSerializer` takes all of this structured data and formats it into a highly readable Markdown document for the final LLM prompt.

**How it improves context:**
LLMs are highly sensitive to prompt formatting. If data is unstructured, the LLM hallucinates file paths or mixes up callers and callees. By explicitly bucketing the data under clear Markdown headers, we force the LLM to understand the architecture boundaries.

**Example Prompt Output:**
```markdown
### Changed Symbols (Methods/Classes):
- **generateOtp** (method) in `src/main/java/.../OtpGeneratorImpl.java`

### Direct Callers (Impacted by these changes):
- `AuthService.loginUser`

### Source code for `generateOtp` in file `src/main/java/.../OtpGeneratorImpl.java`:
...
return "123456"; 
...
```

By strictly defining the `file_path` in the prompt headers, we ensure the LLM's JSON output matches perfectly, allowing the GitHub Publisher to post precise inline comments directly on the PR.
