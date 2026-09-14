import json
from app.services.graph.graph_traversal_service import GraphTraversalService, GraphTraversalConfig

def test_extraction():
    with open('d:/workspace/AI Intelligence Platform/graphify-out/graph.json', 'r') as f:
        ast_data = json.load(f)
        
    modified_files = {"AccountController.java"}
    service = GraphTraversalService()
    
    # 0-Hop Test
    config_0 = GraphTraversalConfig(depth=0)
    subgraph_0 = service.extract_subgraph(ast_data, modified_files, config_0)
    print(f"0-Hop Nodes: {subgraph_0['metadata']['selected_nodes']} | Edges: {subgraph_0['metadata']['selected_edges']}")

    # 1-Hop Test (Both)
    config_1 = GraphTraversalConfig(depth=1, direction="both")
    subgraph_1 = service.extract_subgraph(ast_data, modified_files, config_1)
    print(f"1-Hop (Both) Nodes: {subgraph_1['metadata']['selected_nodes']} | Edges: {subgraph_1['metadata']['selected_edges']}")

    # 1-Hop Test (Outgoing Only)
    config_1_out = GraphTraversalConfig(depth=1, direction="outgoing")
    subgraph_1_out = service.extract_subgraph(ast_data, modified_files, config_1_out)
    print(f"1-Hop (Out) Nodes: {subgraph_1_out['metadata']['selected_nodes']} | Edges: {subgraph_1_out['metadata']['selected_edges']}")

    # 2-Hop Test
    config_2 = GraphTraversalConfig(depth=2, direction="both")
    subgraph_2 = service.extract_subgraph(ast_data, modified_files, config_2)
    print(f"2-Hop (Both) Nodes: {subgraph_2['metadata']['selected_nodes']} | Edges: {subgraph_2['metadata']['selected_edges']}")

if __name__ == "__main__":
    test_extraction()
