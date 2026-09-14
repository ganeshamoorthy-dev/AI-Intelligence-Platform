import hmac
import hashlib
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json
import logging

from app.db.session import get_db
from app.db.models import Project, PullRequest, ReviewRun

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    x_github_hook_id: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    body = await request.body()
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    repo_name = payload.get("repository", {}).get("full_name")
    if not repo_name:
        raise HTTPException(status_code=400, detail="Repository full_name missing")
        
    result = await db.execute(select(Project).filter_by(name=repo_name))
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not registered")
        
    if project.webhook_secret and x_hub_signature_256:
        expected_signature = "sha256=" + hmac.new(
            project.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            pr_data = payload.get("pull_request", {})
            pr_number = pr_data.get("number")
            head_sha = pr_data.get("head", {}).get("sha")
            
            # Upsert PullRequest
            result = await db.execute(select(PullRequest).filter_by(project_id=project.id, pr_number=pr_number))
            pr = result.scalars().first()
            if not pr:
                pr = PullRequest(
                    project_id=project.id,
                    pr_number=pr_number,
                    title=pr_data.get("title", ""),
                    author=pr_data.get("user", {}).get("login", ""),
                    head_sha=head_sha,
                    base_sha=pr_data.get("base", {}).get("sha", ""),
                    status="open"
                )
                db.add(pr)
                await db.commit()
                await db.refresh(pr)
            else:
                pr.head_sha = head_sha
                await db.commit()
                
            # Determine LLM model
            from app.core.config import settings
            from app.db.models import ScmWebhook
            
            model_to_use = settings.LLM_MODEL
            if x_github_hook_id:
                result = await db.execute(select(ScmWebhook).filter_by(provider_hook_id=x_github_hook_id))
                webhook = result.scalars().first()
                if webhook and webhook.llm_model:
                    model_to_use = webhook.llm_model
                    
            # Create ReviewRun
            review_run = ReviewRun(
                pull_request_id=pr.id,
                commit_sha=head_sha,
                status="pending",
                llm_model=model_to_use
            )
            db.add(review_run)
            await db.commit()
            
            logger.info(f"Queued ReviewRun for PR #{pr_number} in {repo_name} from webhook.")
            return {"status": "accepted", "message": "Review queued"}
            
    return {"status": "ignored", "message": "Event ignored"}
