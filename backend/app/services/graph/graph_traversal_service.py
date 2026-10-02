import logging
from copy import deepcopy
from typing import Dict, Any, Set, List, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

IMPORTANT_RELATIONS = [
    "calls",
    "imports",
    "imports_from",
    "references",
    "inherits",
    "extends",
    "implements",
    "uses",
    "re_exports",
]

class GraphTraversalConfig(BaseModel):
    mode: Literal["file", "symbol"] = Field(default="symbol")
    depth: int = Field(default=1, ge=0, le=3, description="0-hop, 1-hop, or 2-hop")
    direction: Literal["incoming", "outgoing", "both"] = Field(default="both")
    relations: List[str] = Field(default_factory=lambda: list(IMPORTANT_RELATIONS))
    max_nodes: int = Field(default=150)
    max_edges: int = Field(default=300)

class GraphTraversalService:
    def extract_subgraph(
        self,
        graph_data: Dict[str, Any],
        modified_files: Set[str],
        config: GraphTraversalConfig = None,
        changed_lines: Dict[str, Set[int]] = None
    ) -> Dict[str, Any]:
        
        if config is None:
            config = GraphTraversalConfig()
        if changed_lines is None:
            changed_lines = {}

        nodes = graph_data.get("nodes", [])
        # NetworkX exports edges as 'links' by default, fallback to edges if present
        edges = graph_data.get("edges") or graph_data.get("links") or []

        if not isinstance(nodes, list):
            raise ValueError("Graphify nodes must be a list")
        if not isinstance(edges, list):
            raise ValueError("Graphify edges must be a list")

        # Normalize changed file paths for lookup
        normalized_files = {
            file_path.replace("\\", "/").lstrip("./")
            for file_path in modified_files
            if file_path
        }
        
        # Normalize changed_lines keys
        normalized_changed_lines = {
            k.replace("\\", "/").lstrip("./"): v
            for k, v in changed_lines.items()
        }

        # --------------------------------------------------
        # 1. Deduce node line ranges and group by file
        # --------------------------------------------------
        def get_start_line(n):
            loc = n.get("source_location")
            if isinstance(loc, str) and loc.startswith("L"):
                try:
                    return int(loc[1:])
                except ValueError:
                    return 0
            return 0

        file_to_nodes = {}
        for node in nodes:
            source_file = str(node.get("source_file") or node.get("file") or node.get("path") or "").replace("\\", "/").lstrip("./")
            if source_file:
                file_to_nodes.setdefault(source_file, []).append(node)
                
        for sf, fnodes in file_to_nodes.items():
            fnodes.sort(key=get_start_line)
            for i, n in enumerate(fnodes):
                n["_start"] = get_start_line(n)
                n["_end"] = None  # Use None instead of float('inf') for JSON compatibility
                if i + 1 < len(fnodes):
                    next_start = get_start_line(fnodes[i+1])
                    if next_start > n["_start"]:
                        n["_end"] = next_start - 1

        # --------------------------------------------------
        # 2. Find nodes inside modified files (0-hop base)
        # --------------------------------------------------
        modified_node_ids = set()
        for node in nodes:
            source_file = str(
                node.get("source_file") or node.get("file") or node.get("path") or ""
            ).replace("\\", "/").lstrip("./")

            if not source_file:
                continue

            # Find matching file in our normalized set
            matching_file = None
            for mf in normalized_files:
                if source_file.endswith(mf) or mf.endswith(source_file):
                    matching_file = mf
                    break

            if matching_file:
                node_id = node.get("id")
                if node_id is None:
                    continue
                    
                if config.mode == "symbol" and matching_file in normalized_changed_lines:
                    lines = normalized_changed_lines[matching_file]
                    if lines:
                        # Check overlap
                        start = node.get("_start", 0)
                        end = node.get("_end")
                        end_val = end if end is not None else 9999999
                        if not any(start <= line <= end_val for line in lines):
                            continue # Skip this symbol!
                            
                modified_node_ids.add(node_id)

        if not modified_node_ids:
            logger.warning(f"No Graphify nodes matched changed files: {normalized_files}")
            return {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "type": f"{config.depth}-hop-subgraph",
                    "reason": "no-file-match",
                    "changed_files": len(normalized_files),
                    "total_nodes": len(nodes),
                    "selected_nodes": 0,
                    "selected_edges": 0
                },
            }

        # --------------------------------------------------
        # 2. BFS Traversal for N hops
        # --------------------------------------------------
        relevant_node_ids = set(modified_node_ids)
        current_frontier = set(modified_node_ids)
        
        allowed_relations = set(config.relations)
        
        for current_depth in range(config.depth):
            if not current_frontier:
                break
                
            next_frontier = set()
            for edge in edges:
                relation = edge.get("relation")
                if relation not in allowed_relations:
                    continue

                source = edge.get("source")
                target = edge.get("target")

                # Direction handling
                if config.direction in ["outgoing", "both"]:
                    if source in current_frontier and target not in relevant_node_ids:
                        next_frontier.add(target)
                        
                if config.direction in ["incoming", "both"]:
                    if target in current_frontier and source not in relevant_node_ids:
                        next_frontier.add(source)

            relevant_node_ids.update(next_frontier)
            current_frontier = next_frontier

        # Enforce limits on node count
        truncated_nodes = False
        if len(relevant_node_ids) > config.max_nodes:
            logger.warning(f"Subgraph exceeds max_nodes limit ({len(relevant_node_ids)} > {config.max_nodes}). Truncating.")
            truncated_nodes = True
            # Keep all modified nodes first
            final_ids = set(modified_node_ids)
            for node_id in relevant_node_ids:
                if len(final_ids) >= config.max_nodes:
                    break
                final_ids.add(node_id)
            relevant_node_ids = final_ids

        # --------------------------------------------------
        # 3. Copy selected nodes and generate explanations (Phase 5)
        # --------------------------------------------------
        filtered_nodes = []
        for node in nodes:
            node_id = node.get("id")
            if node_id in relevant_node_ids:
                copied_node = deepcopy(node)
                is_modified = node_id in modified_node_ids
                copied_node["modified"] = is_modified
                
                # Basic Dependency Explanation
                if is_modified:
                    copied_node["included_because"] = "Directly modified in this Pull Request."
                    copied_node["potential_impact"] = "High"
                else:
                    is_external = node.get("external") or node.get("is_external")
                    f = str(node.get("source_file") or node.get("file") or node.get("path") or "")
                    if "node_modules" in f or "venv" in f or "site-packages" in f or "framework" in f:
                        is_external = True
                        copied_node["is_external"] = True
                        
                    if is_external:
                        copied_node["included_because"] = "External dependency invoked by application code."
                        copied_node["potential_impact"] = "Low (External code is unlikely to break, but integration might)"
                    else:
                        copied_node["included_because"] = "Internal dependency interacting with modified code."
                        copied_node["potential_impact"] = "Medium (Risk of downstream regression)"
                        
                filtered_nodes.append(copied_node)

        # --------------------------------------------------
        # 4. Keep only edges between selected nodes
        # --------------------------------------------------
        filtered_graph_edges = []
        truncated_edges = False
        for edge in edges:
            if len(filtered_graph_edges) >= config.max_edges:
                logger.warning(f"Subgraph exceeds max_edges limit ({config.max_edges}). Truncating edges.")
                truncated_edges = True
                break
                
            relation = edge.get("relation")
            if relation not in allowed_relations:
                continue

            source = edge.get("source")
            target = edge.get("target")

            if source in relevant_node_ids and target in relevant_node_ids:
                filtered_graph_edges.append(edge)

        return {
            "nodes": filtered_nodes,
            "edges": filtered_graph_edges,
            "metadata": {
                "type": f"{config.depth}-hop-subgraph",
                "changed_files": len(normalized_files),
                "total_nodes": len(nodes),
                "selected_nodes": len(filtered_nodes),
                "selected_edges": len(filtered_graph_edges),
                "modified_node_count": len(modified_node_ids),
                "relations": list(allowed_relations),
                "direction": config.direction,
                "depth": config.depth,
                "truncated_nodes": truncated_nodes,
                "truncated_edges": truncated_edges
            },
        }
