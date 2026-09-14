import json
import os
import sys

# Add backend to path
sys.path.append('d:/workspace/AI Intelligence Platform/backend')

from app.services.llm.inference import LlmService

def test_extraction():
    with open('d:/workspace/AI Intelligence Platform/graphify-out/graph.json', 'r') as f:
        ast_data = json.load(f)
        
    print(f"Original graph has {len(ast_data.get('nodes', []))} nodes and {len(ast_data.get('edges', []) or ast_data.get('links', []))} edges.")
    
    svc = LlmService()
    
    # Simulate modifying one file
    modified_files = {"AccountController.java"}
    
    result = svc._extract_1_hop_subgraph(ast_data, modified_files)
    
    print(f"Filtered graph has {len(result.get('nodes', []))} nodes and {len(result.get('edges', []))} edges.")
    
    for node in result.get('nodes', []):
        print(f"- {node.get('id')} ({node.get('source_file')}) modified: {node.get('modified', False)}")

if __name__ == "__main__":
    test_extraction()
