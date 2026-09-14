import logging
from copy import deepcopy
from typing import List, Dict, Any, Set
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

logger = logging.getLogger(__name__)

IMPORTANT_RELATIONS = {
    "calls",
    "imports",
    "imports_from",
    "references",
    "inherits",
    "extends",
    "implements",
    "uses",
    "re_exports",
}

class FindingModel(BaseModel):
    file_path: str = Field(description="The path of the file where the issue was found")
    line_number: int = Field(description="The approximate line number of the issue")
    severity: str = Field(description="Severity of the issue: low, medium, high, or critical")
    category: str = Field(description="Category: security, performance, logic, or style")
    description: str = Field(description="Detailed explanation of the issue")
    suggested_fix: str = Field(description="Code snippet showing how to fix the issue")

class ReviewOutput(BaseModel):
    findings: List[FindingModel] = Field(description="List of issues found in the code")
    blast_radius_summary: str = Field(description="Summary of the blast radius and architectural risk")

class LlmService:
    def __init__(self, model_name: str = "llama3:latest", platform_settings=None):
        self.model_name = model_name
        self.platform_settings = platform_settings
        self.parser = PydanticOutputParser(pydantic_object=ReviewOutput)
        
        self.llm = self._get_llm(model_name, platform_settings)

    def _get_llm(self, model_name: str, platform_settings):
        from app.core.config import settings
        
        openai_key = platform_settings.openai_api_key if platform_settings and platform_settings.openai_api_key else settings.OPENAI_API_KEY
        google_key = platform_settings.google_api_key if platform_settings and platform_settings.google_api_key else settings.GOOGLE_API_KEY
        
        if model_name.startswith("openai/"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name.replace("openai/", ""), temperature=0.2, api_key=openai_key)
        elif model_name.startswith("gemini/"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name.replace("gemini/", ""), temperature=0.2, api_key=google_key)
        elif model_name.startswith("ollama/"):
            return ChatOllama(model=model_name.replace("ollama/", ""), temperature=0.2)
        else:
            # default to ollama
            return ChatOllama(model=model_name, temperature=0.2)

    async def analyze_ast(self, subgraph: Dict[str, Any], pr_diff: str, source_snippets: List[Dict[str, Any]] = None) -> tuple[ReviewOutput, Dict[str, Any], int, int]:
        if source_snippets is None:
            source_snippets = []
            
        custom_instructions = ""
        severity_threshold = "low"
        if self.platform_settings:
            custom_instructions = self.platform_settings.custom_instructions or ""
            severity_threshold = self.platform_settings.severity_threshold or "low"
            
        system_msg = f"You are an expert AI code reviewer evaluating a Pull Request. You have access to the raw diff, the extracted source code of the affected methods, and an AST dependency graph showing the blast radius. Focus on high-value issues, security flaws, and architectural risks. Use the AST graph to understand the blast radius, but use the source code snippets to validate actual logic bugs. Be concise.\nOnly report findings with a severity of {severity_threshold.upper()} or higher.\n{custom_instructions}"
        
        # 1. Formulate Prompt using pre-filtered subgraph and actual source snippets
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("user", "Here is the raw git diff:\n\n{diff}\n\nHere is the actual source code for the affected methods inside the blast radius:\n\n{snippets}\n\nHere is the 1-hop structural dependency subgraph:\n\n{ast}\n\nProvide your code review and explain the blast radius. \n\n{format_instructions}")
        ])
        
        chain = prompt | self.llm | self.parser
        
        try:
            import json
            snippets_str = json.dumps(source_snippets, indent=2)
            
            # 1. Format the prompt
            prompt_val = await prompt.aformat(
                diff=pr_diff[:10000],
                snippets=snippets_str[:30000],
                ast=str(subgraph)[:20000],
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 2. Invoke LLM to get raw AIMessage
            raw_response = await self.llm.ainvoke(prompt_val)
            
            # 3. Parse output
            result = self.parser.parse(raw_response.content)
            
            # 4. Extract tokens (Standardized in Langchain 0.2/0.3 via usage_metadata)
            input_tokens = 0
            output_tokens = 0
            
            if hasattr(raw_response, 'usage_metadata') and raw_response.usage_metadata:
                input_tokens = raw_response.usage_metadata.get("input_tokens", 0)
                output_tokens = raw_response.usage_metadata.get("output_tokens", 0)
            else:
                # Fallbacks for older Ollama or specific provider metadata
                metadata = raw_response.response_metadata or {}
                if "token_usage" in metadata:
                    input_tokens = metadata["token_usage"].get("prompt_tokens", 0)
                    output_tokens = metadata["token_usage"].get("completion_tokens", 0)
                else:
                    input_tokens = metadata.get("prompt_eval_count", 0)
                    output_tokens = metadata.get("eval_count", 0)
            
            logger.info(f"LLM Inference complete. Input Tokens: {input_tokens}, Output Tokens: {output_tokens}. Raw Metadata: {getattr(raw_response, 'response_metadata', None)}")
            return result, subgraph, input_tokens, output_tokens
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return ReviewOutput(findings=[], blast_radius_summary="Failed to analyze code."), subgraph, 0, 0
