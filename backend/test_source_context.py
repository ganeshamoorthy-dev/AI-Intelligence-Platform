import json
import os
from app.services.graph.graph_traversal_service import GraphTraversalService, GraphTraversalConfig
from app.services.graph.source_context_service import SourceContextService

def test_source_extraction():
    with open('d:/workspace/AI Intelligence Platform/graphify-out/graph.json', 'r') as f:
        ast_data = json.load(f)
        
    modified_files = {"AccountController.java"}
    
    # Extract Graph
    service = GraphTraversalService()
    config = GraphTraversalConfig(mode="file", depth=1)
    subgraph = service.extract_subgraph(ast_data, modified_files, config, {})
    
    # Extract Snippets
    workspace = "d:/workspace/AI Intelligence Platform"
    source_service = SourceContextService(max_total_lines=1200, max_lines_per_snippet=10)
    snippets = source_service.extract_snippets(subgraph, workspace)
    
    print(f"Extracted {len(snippets)} snippets.")
    if snippets:
        print("\nFirst Snippet Preview:")
        print(f"File: {snippets[0]['file']}")
        print(f"Lines: {snippets[0]['start_line']} - {snippets[0]['end_line']}")
        print(f"Code:\n{snippets[0]['content']}")

if __name__ == "__main__":
    test_source_extraction()
