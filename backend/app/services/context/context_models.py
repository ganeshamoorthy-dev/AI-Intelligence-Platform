from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ReviewContext(BaseModel):
    changed_files: List[Dict[str, Any]] = Field(default_factory=list)
    changed_symbols: List[Dict[str, Any]] = Field(default_factory=list)

    direct_callers: List[Dict[str, Any]] = Field(default_factory=list)
    direct_callees: List[Dict[str, Any]] = Field(default_factory=list)

    interfaces: List[Dict[str, Any]] = Field(default_factory=list)
    implementations: List[Dict[str, Any]] = Field(default_factory=list)
    related_tests: List[Dict[str, Any]] = Field(default_factory=list)

    external_dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    source_snippets: List[Dict[str, Any]] = Field(default_factory=list)
    graph_relationships: List[Dict[str, Any]] = Field(default_factory=list)

    risk_factors: List[str] = Field(default_factory=list)
    context_summary: str = ""

    def to_dict(self) -> dict:
        return self.model_dump()
