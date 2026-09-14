import json
from app.services.graph.graph_traversal_service import GraphTraversalService, GraphTraversalConfig
from app.services.graph.changed_symbol_service import ChangedSymbolService

def test_symbol_extraction():
    with open('d:/workspace/AI Intelligence Platform/graphify-out/graph.json', 'r') as f:
        ast_data = json.load(f)
        
    # Simulate a diff that ONLY changes line 25 of AccountController.java
    # (Assuming AccountController has a method around line 25, we will see it filter to that symbol)
    mock_diff = """--- a/Backend/src/main/java/com/spring/security/controller/AccountController.java
+++ b/Backend/src/main/java/com/spring/security/controller/AccountController.java
@@ -24,3 +24,3 @@
-    public void oldMethod() {
+    public void newMethod() {
"""

    symbol_service = ChangedSymbolService()
    changed_lines = symbol_service.parse_diff(mock_diff)
    modified_files = set(changed_lines.keys())
    
    print(f"Changed Lines Extracted: {changed_lines}")
    
    service = GraphTraversalService()
    
    print("\n--- FILE LEVEL (Old Way) ---")
    config_file = GraphTraversalConfig(mode="file", depth=1)
    subgraph_file = service.extract_subgraph(ast_data, modified_files, config_file, changed_lines)
    print(f"0-Hop Modified Nodes: {subgraph_file['metadata']['modified_node_count']}")
    
    print("\n--- SYMBOL LEVEL (New Way) ---")
    config_symbol = GraphTraversalConfig(mode="symbol", depth=1)
    subgraph_symbol = service.extract_subgraph(ast_data, modified_files, config_symbol, changed_lines)
    print(f"0-Hop Modified Nodes: {subgraph_symbol['metadata']['modified_node_count']}")

if __name__ == "__main__":
    test_symbol_extraction()
