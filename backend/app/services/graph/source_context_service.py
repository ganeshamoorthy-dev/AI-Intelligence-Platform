import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SourceContextService:
    def __init__(self, max_total_lines: int = 10000, max_lines_per_snippet: int = 500):
        self.max_total_lines = max_total_lines
        self.max_lines_per_snippet = max_lines_per_snippet

    def extract_snippets(self, subgraph: Dict[str, Any], workspace_path: str) -> List[Dict[str, Any]]:
        """
        Iterates over the nodes in the subgraph, opens the files in the workspace,
        and extracts the exact source code for each node.
        """
        nodes = subgraph.get("nodes", [])
        snippets = []
        total_lines_extracted = 0

        # Sort nodes by modified first, so we prioritize getting source code for changed symbols
        sorted_nodes = sorted(nodes, key=lambda n: not n.get("modified", False))

        for node in sorted_nodes:
            if total_lines_extracted >= self.max_total_lines:
                logger.warning(f"Source context limit reached ({self.max_total_lines} lines). Stopping extraction.")
                break

            source_file = node.get("source_file") or node.get("file") or node.get("path")
            if not source_file:
                continue
                
            start_line = node.get("_start", 0)
            end_line = node.get("_end")
            
            if start_line == 0:
                continue # Unknown location

            # Constrain end line
            if end_line is None:
                end_line = start_line + self.max_lines_per_snippet
            
            # Cap snippet size
            if (end_line - start_line) > self.max_lines_per_snippet:
                end_line = start_line + self.max_lines_per_snippet

            absolute_path = os.path.join(workspace_path, source_file)
            
            if not os.path.exists(absolute_path):
                logger.warning(f"File not found in workspace: {absolute_path}")
                continue

            try:
                with open(absolute_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Lines are 0-indexed in python, but 1-indexed in source_location
                start_idx = max(0, start_line - 1)
                end_idx = min(len(lines), int(end_line))
                
                snippet_lines = lines[start_idx:end_idx]
                snippet_content = "".join(snippet_lines)
                
                if snippet_content.strip():
                    snippets.append({
                        "node_id": node.get("id"),
                        "file": source_file,
                        "start_line": start_line,
                        "end_line": end_idx,
                        "modified": node.get("modified", False),
                        "content": snippet_content
                    })
                    total_lines_extracted += len(snippet_lines)
                    
            except Exception as e:
                logger.error(f"Failed to read source file {absolute_path}: {e}")

        logger.info(f"Extracted {len(snippets)} source snippets ({total_lines_extracted} total lines).")
        return snippets
