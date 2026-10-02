from typing import Dict, Any, List
import logging

from .context_models import ReviewContext
from .context_ranker import ContextRanker
from .context_serializer import ContextSerializer
from app.services.graph.dependency_classifier import DependencyClassifier

logger = logging.getLogger(__name__)

class ContextEngine:
    def __init__(self):
        self.classifier = DependencyClassifier()
        self.ranker = ContextRanker()
        self.serializer = ContextSerializer()
        
    def build_context(self, subgraph: Dict[str, Any], changed_symbols: List[Dict[str, Any]]) -> ReviewContext:
        """
        Takes the extracted subgraph and structured changes, classifies dependencies, 
        gathers source snippets, and builds a ranked ReviewContext object.
        """
        logger.info("Building structured ReviewContext")
        
        changed_symbol_ids = {s.get("symbol_id") for s in changed_symbols if s.get("symbol_id")}
        
        # 1. Classify Dependencies
        categorized = self.classifier.classify(subgraph, changed_symbol_ids)
        
        # 2. Extract Source Snippets (already attached to subgraph by SourceContextService)
        source_snippets = subgraph.get("source_snippets", [])
        
        # 3. Assess basic risk factors
        risk_factors = []
        if categorized["direct_callers"]:
            risk_factors.append(f"Changes impact {len(categorized['direct_callers'])} downstream dependencies (callers).")
        if categorized["external_dependencies"]:
            risk_factors.append("Changes interact with external frameworks/libraries.")
            
        summary = f"Review includes {len(changed_symbols)} changed symbols, impacting {len(categorized['direct_callers'])} callers."
        
        # 4. Construct initial context
        context = ReviewContext(
            changed_files=[], # Can be populated if needed
            changed_symbols=changed_symbols,
            direct_callers=categorized["direct_callers"],
            direct_callees=categorized["direct_callees"],
            interfaces=categorized["interfaces"],
            implementations=categorized["implementations"],
            related_tests=categorized["related_tests"],
            external_dependencies=categorized["external_dependencies"],
            source_snippets=source_snippets,
            graph_relationships=subgraph.get("edges", []),
            risk_factors=risk_factors,
            context_summary=summary
        )
        
        # 5. Rank and filter
        context = self.ranker.rank_and_filter(context)
        
        return context
        
    def serialize(self, context: ReviewContext) -> str:
        return self.serializer.format_for_llm(context)
