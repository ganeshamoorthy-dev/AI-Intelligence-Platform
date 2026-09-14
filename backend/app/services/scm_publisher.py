import httpx
import logging
from typing import Optional
from app.core.config import settings
from app.services.llm_inference import PRReviewOutput

logger = logging.getLogger(__name__)

async def publish_github_review(
    repo_full_name: str, 
    pr_number: int, 
    commit_sha: str, 
    review_output: PRReviewOutput
) -> Optional[str]:
    """
    Publishes the structured findings from the LLM back to GitHub as a Pull Request Review.
    """
    token = settings.GITHUB_WEBHOOK_SECRET  # In a real app, this should be a dedicated GITHUB_PAT
    if not token or token == "your_super_secret_webhook_key":
        logger.warning("No valid GitHub PAT configured. Skipping SCM publishing.")
        return None
        
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    comments = []
    for finding in review_output.findings:
        if finding.line_number:
            body = f"**[{finding.severity.upper()}] {finding.category.capitalize()} Issue**\n\n{finding.description}"
            if finding.suggested_fix:
                body += f"\n\n*Suggested Fix:*\n```\n{finding.suggested_fix}\n```"
                
            comments.append({
                "path": finding.file_path,
                "line": finding.line_number,
                "body": body
            })
            
    if not comments:
        logger.info("No findings to publish to GitHub.")
        return None
        
    payload = {
        "commit_id": commit_sha,
        "event": "COMMENT",
        "body": f"AI Developer Intelligence Platform found {len(comments)} issues.",
        "comments": comments
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully published review for PR {pr_number}")
            return response.json().get("html_url")
    except httpx.HTTPStatusError as e:
        logger.error(f"GitHub API error ({e.response.status_code}): {e.response.text}")
    except Exception as e:
        logger.error(f"Failed to publish to GitHub: {e}")
        
    return None
