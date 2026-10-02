from .context_models import ReviewContext

class ContextSerializer:
    def format_for_llm(self, context: ReviewContext) -> str:
        """
        Takes the structured ReviewContext and formats it into a highly readable markdown string for the LLM prompt.
        """
        lines = []
        
        lines.append("## Changed Code Context\n")
        lines.append(context.context_summary)
        lines.append("\n")
        
        if context.risk_factors:
            lines.append("### Risk Factors:")
            for rf in context.risk_factors:
                lines.append(f"- {rf}")
            lines.append("\n")
            
        if context.changed_symbols:
            lines.append("### Changed Symbols (Methods/Classes):")
            for cs in context.changed_symbols:
                name = cs.get("symbol_name") or cs.get("id") or "Unknown"
                stype = cs.get("symbol_type") or "symbol"
                fpath = cs.get("file_path") or "Unknown file"
                lines.append(f"- **{name}** ({stype}) in `{fpath}`")
            lines.append("\n")
            
        if context.direct_callers:
            lines.append("### Direct Callers (Impacted by these changes):")
            for node in context.direct_callers:
                name = node.get("label") or node.get("id") or "Unknown"
                lines.append(f"- {name}")
            lines.append("\n")
            
        if context.direct_callees:
            lines.append("### Direct Callees (Dependencies of the changed code):")
            for node in context.direct_callees:
                name = node.get("label") or node.get("id") or "Unknown"
                lines.append(f"- {name}")
            lines.append("\n")
            
        if context.related_tests:
            lines.append("### Related Tests:")
            for node in context.related_tests:
                name = node.get("label") or node.get("id") or "Unknown"
                lines.append(f"- {name}")
            lines.append("\n")
            
        if context.source_snippets:
            lines.append("### Source Snippets:")
            for snippet in context.source_snippets:
                node_id = snippet.get("node_id")
                content = snippet.get("content")
                if content:
                    file_path = snippet.get("file", "Unknown")
                    lines.append(f"**Source code for `{node_id}` in file `{file_path}`**:")
                    lines.append("```")
                    lines.append(content.strip())
                    lines.append("```\n")
                    
        return "\n".join(lines)
