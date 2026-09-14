import logging
from typing import Dict, List, Tuple

try:
    import graphify
except ImportError:
    # Fallback/Mock for local dev if graphify isn't installed
    graphify = None

logger = logging.getLogger(__name__)

MAX_CONTEXT_TOKENS = 3000
    
def extract_1_hop_context(
    workspace_path: str, 
    modified_files: Dict[str, List[Tuple[int, int]]]
) -> Dict[str, str]:
    """
    Uses Graphify to parse the AST of modified files, finding the 
    functions/classes that intersect with the modified line ranges, 
    and extracting their 1-hop dependencies (imports and call sites).   
    """
    context_payloads = {}
    
    if not graphify:
        logger.warning("Graphify is not installed. Using mocked context builder.")
        for file_path, ranges in modified_files.items():
            context_payloads[file_path] = f"// Mocked context for {file_path} modifications: {ranges}"
        return context_payloads
        
    try:
        # Initialize Graphify engine on the workspace
        engine = graphify.Engine(project_root=workspace_path)
        
        for file_path, ranges in modified_files.items():
            file_ast = engine.parse_file(file_path)
            
            snippets = []
            current_tokens = 0
            
            for (start, end) in ranges:
                # Find the AST node containing the changes
                node = file_ast.find_node_at_range(start, end)
                if not node:
                    continue
                
                # Extract the 1-hop context
                context_graph = engine.get_1_hop_context(node)
                
                snippet = context_graph.to_code_string()
                
                # Naive token estimation (1 token ~= 4 chars)
                estimated_tokens = len(snippet) // 4
                
                if current_tokens + estimated_tokens > MAX_CONTEXT_TOKENS:
                    snippets.append("// [Truncated: Context Budget Exceeded]")
                    break
                    
                snippets.append(snippet)
                current_tokens += estimated_tokens
                
            context_payloads[file_path] = "\n\n".join(snippets)
            
    except Exception as e:
        logger.error(f"Graphify context extraction failed: {e}")
        
    return context_payloads
