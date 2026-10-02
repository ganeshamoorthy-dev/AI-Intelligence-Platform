from typing import List, Dict, Any

class DependencyClassifier:
    """
    Classifies nodes and edges into meaningful categories (callers, callees, external, tests, etc.)
    """
    def classify(self, subgraph: Dict[str, Any], changed_symbol_ids: set) -> Dict[str, List[Dict[str, Any]]]:
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        
        node_map = {n.get("id"): n for n in nodes if n.get("id")}
        
        categorized = {
            "direct_callers": [],
            "direct_callees": [],
            "interfaces": [],
            "implementations": [],
            "related_tests": [],
            "external_dependencies": [],
            "other": []
        }
        
        seen = set()
        
        def is_external(node):
            if node.get("external") or node.get("is_external"):
                return True
            # Fallback heuristic
            f = str(node.get("source_file") or node.get("file") or node.get("path") or "")
            if "node_modules" in f or "venv" in f or "site-packages" in f or "framework" in f:
                return True
            return False

        def is_test(node):
            name = str(node.get("label") or node.get("name") or "").lower()
            f = str(node.get("source_file") or node.get("file") or node.get("path") or "").lower()
            return "test" in name or "test" in f
            
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            relation = str(edge.get("relation") or edge.get("type") or "").lower()
            
            source_node = node_map.get(source_id)
            target_node = node_map.get(target_id)
            
            if not source_node or not target_node:
                continue
                
            # If target is changed, and source is calling it -> source is caller
            if target_id in changed_symbol_ids and source_id not in changed_symbol_ids:
                if source_id not in seen:
                    if is_test(source_node):
                        categorized["related_tests"].append(source_node)
                    elif is_external(source_node):
                        categorized["external_dependencies"].append(source_node)
                    elif relation in ["calls", "uses", "references"]:
                        categorized["direct_callers"].append(source_node)
                    elif relation in ["implements", "extends"]:
                        categorized["implementations"].append(source_node)
                    else:
                        categorized["other"].append(source_node)
                    seen.add(source_id)
                    
            # If source is changed, and it calls target -> target is callee
            if source_id in changed_symbol_ids and target_id not in changed_symbol_ids:
                if target_id not in seen:
                    if is_test(target_node):
                        categorized["related_tests"].append(target_node)
                    elif is_external(target_node):
                        categorized["external_dependencies"].append(target_node)
                    elif relation in ["calls", "uses", "references"]:
                        categorized["direct_callees"].append(target_node)
                    elif relation in ["implements", "extends"]:
                        categorized["interfaces"].append(target_node)
                    else:
                        categorized["other"].append(target_node)
                    seen.add(target_id)
                    
        return categorized
