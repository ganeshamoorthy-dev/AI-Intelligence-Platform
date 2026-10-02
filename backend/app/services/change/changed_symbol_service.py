from typing import List, Dict, Any
from .change_models import ChangedSymbol

class ChangedSymbolService:
    def extract_symbols_for_file(self, file_path: str, changed_lines: List[int], graph_data: Dict[str, Any]) -> List[ChangedSymbol]:
        """
        Given a file path and its changed lines, find which AST nodes (symbols) overlap with those lines.
        """
        symbols = []
        nodes = graph_data.get("nodes", [])
        
        # Filter nodes belonging to the given file
        file_nodes = []
        for node in nodes:
            # Nodes might have 'file', 'source_file', 'path'
            node_file = node.get("file") or node.get("source_file") or node.get("path")
            if not node_file:
                continue
            # Handle normalized paths
            if file_path.endswith(node_file.split('/')[-1]): # Basic heuristic if paths differ slightly
                if node_file.replace('\\', '/').endswith(file_path.replace('\\', '/')):
                    file_nodes.append(node)
                elif file_path.replace('\\', '/').endswith(node_file.replace('\\', '/')):
                    file_nodes.append(node)
                    
        # Now find intersecting nodes
        for node in file_nodes:
            # We want to identify meaningful symbols: functions, classes, interfaces
            is_symbol = node.get("_callable") or node.get("_class") or node.get("_callable_class") or node.get("type", "").lower() in ["method", "function", "class", "interface", "constructor"]
            if not is_symbol:
                continue
                
            start_line = node.get("start_line")
            end_line = node.get("end_line")
            
            # Fallback if Graphify uses source_location e.g. "10:1-20:5"
            if start_line is None and "source_location" in node:
                loc = node["source_location"]
                if isinstance(loc, str) and ":" in loc:
                    try:
                        parts = loc.split('-')
                        start_line = int(parts[0].split(':')[0])
                        if len(parts) > 1:
                            end_line = int(parts[1].split(':')[0])
                    except:
                        pass
                        
            if start_line is None:
                continue
                
            if end_line is None:
                end_line = start_line
                
            # Find intersection of changed_lines and node's line range
            intersecting_lines = [line for line in changed_lines if start_line <= line <= end_line]
            
            if intersecting_lines:
                symbol_type = "symbol"
                if node.get("_callable_class") or node.get("_class") or node.get("type", "").lower() == "class":
                    symbol_type = "class"
                elif node.get("_callable") or node.get("type", "").lower() in ["method", "function"]:
                    symbol_type = "method"
                elif node.get("type"):
                    symbol_type = str(node.get("type")).lower()
                    
                symbols.append(
                    ChangedSymbol(
                        file_path=file_path,
                        symbol_id=node.get("id"),
                        symbol_name=node.get("label") or node.get("name") or node.get("id", "Unknown"),
                        symbol_type=symbol_type,
                        start_line=start_line,
                        end_line=end_line,
                        change_type="modified", # Simplification: could enhance to detect 'added' or 'deleted' based on diff context
                        changed_lines=intersecting_lines
                    )
                )
                
        return symbols
