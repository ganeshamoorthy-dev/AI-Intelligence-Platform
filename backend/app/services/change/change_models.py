from pydantic import BaseModel
from typing import List, Optional, Literal

class ChangedSymbol(BaseModel):
    file_path: str
    symbol_id: Optional[str] = None
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: Optional[int] = None
    change_type: str # added, modified, deleted, etc.
    changed_lines: List[int]

class ChangedFileAnalysis(BaseModel):
    file_path: str
    changed_lines: List[int]
    changed_symbols: List[ChangedSymbol]

class ChangeAnalysis(BaseModel):
    changed_files: List[ChangedFileAnalysis]
    
    def to_dict(self) -> dict:
        return self.model_dump()
