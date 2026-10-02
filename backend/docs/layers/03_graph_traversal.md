# Layer 3: Graph Traversal (Blast Radius)

## Purpose
To find hidden integration bugs, the LLM needs to see code that *wasn't* modified in the PR, but is directly impacted by the changes. The GraphTraversalService calculates this "Blast Radius."

## How It Works
Using the modified nodes identified in Layer 2 as the starting point, the service performs a breadth-first search on the AST graph:
1. **Direct Callers:** Traces calls edges backwards (incoming) to see what invokes the changed code.
2. **Direct Callees:** Traces calls edges forwards (outgoing) to see what the changed code depends on.
3. **Tests:** Identifies test suites related to the modified classes.

## Output
A subgraph containing only the modified nodes and their immediate 1-hop or 2-hop dependencies. This aggressively shrinks the repository size while preserving vital context.
