from .context_models import ReviewContext

class ContextRanker:
    def rank_and_filter(self, context: ReviewContext, max_tokens: int = 15000) -> ReviewContext:
        """
        Applies heuristics to truncate or filter the context so it fits within LLM token limits,
        prioritizing the most important files and relationships.
        """
        # Simplistic ranking/truncation for now
        
        # Sort snippets by priority: Changed code > Callers > Callees > Tests > External
        # For Phase 3, we just implement a basic hard cap
        
        MAX_SNIPPETS = 20
        if len(context.source_snippets) > MAX_SNIPPETS:
            context.source_snippets = context.source_snippets[:MAX_SNIPPETS]
            context.risk_factors.append(f"Context was truncated: omitted {len(context.source_snippets) - MAX_SNIPPETS} source snippets.")
            
        return context
