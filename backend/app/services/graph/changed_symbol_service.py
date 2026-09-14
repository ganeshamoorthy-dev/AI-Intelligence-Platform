import logging
import re
from typing import Dict, Set

logger = logging.getLogger(__name__)

class ChangedSymbolService:
    def parse_diff(self, diff_text: str) -> Dict[str, Set[int]]:
        """
        Parses a unified diff and returns a mapping of file paths to a set of changed line numbers.
        """
        changed_lines: Dict[str, Set[int]] = {}
        
        current_file = None
        current_line_num = 0
        
        for line in diff_text.split('\n'):
            if line.startswith('+++ b/'):
                current_file = line[6:].strip()
                changed_lines[current_file] = set()
            elif line.startswith('--- a/'):
                pass
            elif line.startswith('@@ '):
                # Parse @@ -x,y +a,b @@
                match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match and current_file:
                    current_line_num = int(match.group(1))
            elif current_file:
                if line.startswith('+'):
                    changed_lines[current_file].add(current_line_num)
                    current_line_num += 1
                elif line.startswith('-'):
                    # We can't map deleted lines to the NEW AST easily, so we just track the location
                    # where the deletion happened as a change.
                    changed_lines[current_file].add(current_line_num)
                elif not line.startswith('\\ No newline'):
                    current_line_num += 1
                    
        return changed_lines
