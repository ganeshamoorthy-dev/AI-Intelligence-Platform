from typing import Dict, Any
from .change_models import ChangeAnalysis, ChangedFileAnalysis
from .diff_hunk_service import DiffHunkService
from .changed_file_service import ChangedFileService

class ChangeAnalyzer:
    def __init__(self):
        self.diff_service = DiffHunkService()
        self.file_service = ChangedFileService()
        
    def analyze(self, diff_data: str, graph_data: Dict[str, Any]) -> ChangeAnalysis:
        """
        Analyzes a git diff alongside AST graph data to produce a structured understanding
        of exactly which semantic symbols were changed in which files.
        """
        # 1. Extract changed files and lines from raw diff
        changed_lines_map = self.diff_service.extract_changed_lines(diff_data)
        
        changed_files = []
        
        # 2. For each changed file, map lines to AST symbols
        for file_path, lines in changed_lines_map.items():
            file_analysis = self.file_service.analyze_file(file_path, lines, graph_data)
            changed_files.append(file_analysis)
            
        return ChangeAnalysis(changed_files=changed_files)
