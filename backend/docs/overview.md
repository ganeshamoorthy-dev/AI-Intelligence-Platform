# Antigravity AI: Context Engine Overview

The Context Engine is the core intelligence component of the Antigravity Code Review Platform. It solves the LLM context window problem through a 5-layer pipeline that transforms raw repositories and fragmented diffs into structured, high-signal prompts.

## The 5 Layers
1. **Layer 1 (Semantic Parsing):** Converts code to an AST graph.
2. **Layer 2 (Change Analysis):** Maps Git diffs to AST nodes.
3. **Layer 3 (Graph Traversal):** Calculates the Blast Radius (callers/callees).
4. **Layer 4 (Source Extraction):** Retrieves code within strict safety limits.
5. **Layer 5 (Serialization):** Formats the data into markdown for LLM ingestion.

Explore the layers/ directory for deep-dive technical documentation on each step.
