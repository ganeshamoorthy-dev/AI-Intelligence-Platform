import httpx
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.db.session import get_db
from app.db.models import ScmAccount
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_github_token(scm_account_id: Optional[int], db: AsyncSession) -> str:
    if scm_account_id:
        acc = await db.scalar(select(ScmAccount).where(ScmAccount.id == scm_account_id))
        if acc:
            return acc.access_token
    if not settings.GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="GitHub PAT is not configured.")
    return settings.GITHUB_WEBHOOK_SECRET

def get_github_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

@router.get("/repos", response_model=List[Dict[str, Any]])
async def list_repositories(scm_account_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Fetches repositories accessible to the configured GitHub PAT or SCM account."""
    token = await get_github_token(scm_account_id, db)
    url = "https://api.github.com/user/repos?sort=updated&per_page=100"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=get_github_headers(token))
        if resp.status_code != 200:
            logger.error(f"GitHub API Error: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch repositories from GitHub")
        
        repos = resp.json()
        return [{"full_name": repo["full_name"], "name": repo["name"]} for repo in repos]

@router.get("/repos/{owner}/{repo}/pulls", response_model=List[Dict[str, Any]])
async def list_pull_requests(owner: str, repo: str, scm_account_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Fetches open pull requests for a specific repository."""
    token = await get_github_token(scm_account_id, db)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&sort=updated&direction=desc"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=get_github_headers(token))
        if resp.status_code != 200:
            logger.error(f"GitHub API Error: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch PRs from GitHub")
        
        prs = resp.json()
        return [
            {
                "number": pr["number"],
                "title": pr["title"],
                "html_url": pr["html_url"],
                "author": pr["user"]["login"]
            } for pr in prs
        ]

