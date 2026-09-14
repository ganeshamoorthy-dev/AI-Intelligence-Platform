from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.db.models import ScmAccount, ScmWebhook, Project
from app.services.scm.github import GithubScmService

logger = logging.getLogger(__name__)

router = APIRouter()

class ScmAccountCreate(BaseModel):
    name: str
    provider: str
    access_token: str

from typing import Optional

class WebhookCreate(BaseModel):
    scm_account_id: int
    repository_url: str
    llm_model: Optional[str] = None

@router.get("/")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScmAccount).where(ScmAccount.is_active == True))
    accounts = result.scalars().all()
    return [
        {
            "id": acc.id,
            "name": acc.name,
            "provider": acc.provider,
            "created_at": acc.created_at
        } for acc in accounts
    ]

@router.post("/")
async def create_account(account: ScmAccountCreate, db: AsyncSession = Depends(get_db)):
    new_acc = ScmAccount(
        name=account.name,
        provider=account.provider,
        access_token=account.access_token
    )
    db.add(new_acc)
    await db.commit()
    await db.refresh(new_acc)
    return {"id": new_acc.id, "name": new_acc.name}

@router.post("/webhooks/register")
async def register_webhook(req: WebhookCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a webhook on the SCM provider and saves it in the database.
    """
    # 1. Get Account
    result = await db.execute(select(ScmAccount).where(ScmAccount.id == req.scm_account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="SCM Account not found")
        
    if account.provider != "github":
        raise HTTPException(status_code=400, detail="Only GitHub is supported for webhooks currently")
        
    scm = GithubScmService(token=account.access_token)
    
    # 2. Get or Create Project
    result = await db.execute(select(Project).where(Project.repository_url == req.repository_url))
    project = result.scalars().first()
    
    if not project:
        metadata = await scm.parse_pr_url(req.repository_url) # Quick hack to get repo_full_name
        repo_full_name = metadata["repo_full_name"]
        
        project = Project(
            name=repo_full_name,
            scm_provider="github",
            repository_url=req.repository_url,
            scm_account_id=account.id
        )
        db.add(project)
        await db.flush()
    else:
        repo_full_name = project.name
        
    # 3. Register Webhook via GitHub API
    try:
        import uuid
        secret = str(uuid.uuid4())
        webhook_data = await scm.register_webhook(repo_full_name, secret)
        
        # 4. Save to DB
        webhook = ScmWebhook(
            project_id=project.id,
            provider_hook_id=str(webhook_data.get("id")),
            secret_token=secret,
            events={"events": webhook_data.get("events", [])},
            llm_model=req.llm_model
        )
        db.add(webhook)
        await db.commit()
        return {"status": "success", "webhook_id": webhook.id}
    except Exception as e:
        logger.error(f"Failed to register webhook: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks")
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScmWebhook, Project, ScmAccount)
        .join(Project, ScmWebhook.project_id == Project.id)
        .outerjoin(ScmAccount, Project.scm_account_id == ScmAccount.id)
    )
    rows = result.all()
    return [
        {
            "id": row.ScmWebhook.id,
            "project_name": row.Project.name,
            "repository_url": row.Project.repository_url,
            "provider_hook_id": row.ScmWebhook.provider_hook_id,
            "events": row.ScmWebhook.events.get("events", []) if row.ScmWebhook.events else [],
            "account_name": row.ScmAccount.name if row.ScmAccount else "Unknown",
            "llm_model": row.ScmWebhook.llm_model,
            "created_at": row.ScmWebhook.created_at
        } for row in rows
    ]
