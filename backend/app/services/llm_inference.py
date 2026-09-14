import logging
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReviewFindingSchema(BaseModel):
    file_path: str = Field(description="The path of the file being reviewed.")
    line_number: Optional[int] = Field(description="The specific line number containing the issue, if applicable.")
    severity: str = Field(description="Severity of the issue: low, medium, high, or critical.")
    category: str = Field(description="Category of the issue: security, performance, logic, or style.")
    description: str = Field(description="A detailed explanation of the problem found.")
    suggested_fix: Optional[str] = Field(description="Markdown formatted code snippet proposing a fix.")

class PRReviewOutput(BaseModel):
    findings: List[ReviewFindingSchema] = Field(description="A list of findings/issues discovered in the PR context.")

def evaluate_pr_context(context_payloads: Dict[str, str]) -> PRReviewOutput:
    """
    Passes the 1-hop AST context payload to the local Ollama LLM to perform a code review.
    Enforces a strict JSON output mapped to the PRReviewOutput schema.
    """
    if not context_payloads:
        return PRReviewOutput(findings=[])
        
    parser = PydanticOutputParser(pydantic_object=PRReviewOutput)
    
    # Format the context into a string
    context_str = ""
    for file_path, context in context_payloads.items():
        context_str += f"\n--- File: {file_path} ---\n{context}\n"
    
    prompt = PromptTemplate(
        template="You are an expert code reviewer prioritizing security, performance, and best practices.\n"
                 "Review the following code changes and their 1-hop dependencies.\n"
                 "{format_instructions}\n\n"
                 "CODE CONTEXT:\n{context}\n",
        input_variables=["context"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    # Initialize ChatOllama running in JSON mode
    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0.1, # Low temperature for more deterministic reviews
        format="json"
    )
    
    chain = prompt | llm | parser
    
    try:
        logger.info(f"Sending {len(context_payloads)} file contexts to LLM ({settings.LLM_MODEL}).")
        result = chain.invoke({"context": context_str})
        return result
    except OutputParserException as e:
        logger.error(f"Failed to parse LLM output: {e}")
        # In a robust system, we would implement a retry loop or self-correction chain here
        return PRReviewOutput(findings=[])
    except Exception as e:
        logger.error(f"LLM inference error: {e}")
        return PRReviewOutput(findings=[])
