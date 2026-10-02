# Layer 4: Source Context Service

## Purpose
Once the Blast Radius is defined, the engine must fetch the actual source code for those specific nodes. SourceContextService handles file extraction and safety limits.

## How It Works
1. Iterates over the nodes in the Blast Radius subgraph.
2. Opens the corresponding files in the ephemeral workspace.
3. Extracts lines _start to _end for each node.
4. **Safety Limits:** It enforces a hard stop (e.g., max_total_lines = 10000) to prevent LLM Context Window overflows and Out-Of-Memory (OOM) crashes.

## Output
A list of source_snippets containing the exact code strings needed by the LLM.
