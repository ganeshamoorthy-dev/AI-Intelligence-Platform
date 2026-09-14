import subprocess
import re
from typing import List, Dict, Tuple

def get_modified_files_and_ranges(workspace_path: str, head_sha: str, base_sha: str) -> Dict[str, List[Tuple[int, int]]]:
    """
    Runs git diff to find modified files and the line ranges that were changed.
    Returns a dictionary mapping file paths to lists of (start_line, end_line) tuples.
    """
    # Fetch the necessary commits
    subprocess.run(["git", "-C", workspace_path, "fetch", "origin", head_sha], check=True, capture_output=True)
    subprocess.run(["git", "-C", workspace_path, "fetch", "origin", base_sha], check=True, capture_output=True)
    
    # Run git diff
    cmd = ["git", "-C", workspace_path, "diff", f"{base_sha}...{head_sha}", "-U0"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    
    diff_output = result.stdout
    
    modified_files = {}
    current_file = None
    
    # Regex to match the file path and chunk headers
    # +++ b/path/to/file.py
    # @@ -5,0 +6,2 @@
    file_regex = re.compile(r'^\+\+\+ b/(.+)$')
    chunk_regex = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    
    for line in diff_output.splitlines():
        file_match = file_regex.match(line)
        if file_match:
            current_file = file_match.group(1)
            modified_files[current_file] = []
            continue
            
        chunk_match = chunk_regex.match(line)
        if chunk_match and current_file:
            start_line = int(chunk_match.group(1))
            length_group = chunk_match.group(2)
            length = int(length_group) if length_group else 1
            
            # If length is 0, it means lines were only deleted. We can skip or record as needed.
            if length > 0:
                end_line = start_line + length - 1
                modified_files[current_file].append((start_line, end_line))
                
    return modified_files
