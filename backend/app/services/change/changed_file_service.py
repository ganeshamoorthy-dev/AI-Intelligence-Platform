from typing import Dict, List
from .change_models import ChangedFileAnalysis
from .changed_symbol_service import ChangedSymbolService

class ChangedFileService:
    def __init__(self):
        self.symbol_service = ChangedSymbolService()
        
    def analyze_file(self, file_path: str, changed_lines: List[int], graph_data: Dict) -> ChangedFileAnalysis:
        symbols = self.symbol_service.extract_symbols_for_file(file_path, changed_lines, graph_data)
        return ChangedFileAnalysis(
            file_path=file_path,
            changed_lines=changed_lines,
            changed_symbols=symbols
        )
