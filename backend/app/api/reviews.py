from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import logging
from typing import Optional

from app.db.session import get_db
from app.db.models import ReviewRun, Project, PullRequest, ReviewFinding, SCMProvider
from app.services.scm.github import GithubScmService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class TriggerReviewRequest(BaseModel):
    pr_url: str
    scm_provider: str = "github"
    scm_account_id: Optional[int] = None
    llm_model: Optional[str] = None

@router.post("/trigger")
async def trigger_review(request: TriggerReviewRequest, db: AsyncSession = Depends(get_db)):
    """
    Triggers an asynchronous PR Review.
    Accepts a PR URL, queues the job, and returns a tracking ID immediately.
    """
    if request.scm_provider != "github":
        raise HTTPException(status_code=400, detail="Only github is supported currently")
        
    token = settings.GITHUB_WEBHOOK_SECRET
    if request.scm_account_id:
        from app.db.models import ScmAccount
        acc = await db.scalar(select(ScmAccount).where(ScmAccount.id == request.scm_account_id))
        if acc:
            token = acc.access_token

    scm = GithubScmService(token=token)
    
    try:
        # 1. Parse URL & Fetch Metadata
        metadata = await scm.parse_pr_url(request.pr_url)
        
        # 2. Get or Create Project
        result = await db.execute(select(Project).filter_by(repository_url=metadata["clone_url"]))
        project = result.scalars().first()
        if not project:
            project = Project(
                name=metadata["repo_full_name"],
                scm_provider=SCMProvider.github,
                repository_url=metadata["clone_url"],
                scm_account_id=request.scm_account_id
            )
            db.add(project)
            await db.flush() # flush to get project.id
            
        # 3. Get or Create PullRequest
        result = await db.execute(
            select(PullRequest).filter_by(project_id=project.id, pr_number=metadata["pr_number"])
        )
        pr = result.scalars().first()
        if not pr:
            pr = PullRequest(
                project_id=project.id,
                pr_number=metadata["pr_number"],
                title=metadata["title"],
                author=metadata["author"],
                head_sha=metadata["commit_sha"],
                base_sha=metadata["base_sha"]
            )
            db.add(pr)
            await db.flush()
            
        # 4. Create Pending ReviewRun Job
        model_to_use = request.llm_model if request.llm_model else settings.LLM_MODEL
        job = ReviewRun(
            pull_request_id=pr.id,
            commit_sha=metadata["commit_sha"],
            status="pending",
            llm_model=model_to_use
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return {"status": "accepted", "run_id": job.id, "message": "Review job queued successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Trigger review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}/status")
async def get_review_status(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewRun).filter_by(id=run_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Review run not found")
        
    return {
        "run_id": job.id,
        "status": job.status,
        "error": job.error_message,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }

@router.get("/{run_id}/results")
async def get_review_results(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewRun).filter_by(id=run_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Review run not found")
        
    if job.status not in ["completed", "completed_publish_failed"]:
        raise HTTPException(status_code=400, detail=f"Review is currently {job.status}. Cannot fetch results yet.")
        
    result = await db.execute(select(ReviewFinding).filter_by(review_run_id=run_id))
    findings = result.scalars().all()
    
    return {
        "run_id": run_id,
        "findings": [
            {
                "id": f.id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity,
                "category": f.category,
                "description": f.description,
                "suggested_fix": f.suggested_fix
            } for f in findings
        ]
    }

class ReviewSummary(BaseModel):
    review_id: str
    status: str
    repository: str
    pull_request_number: int

    changed_files_count: int
    changed_lines_count: int
    changed_symbols_count: int

    affected_files_count: int
    affected_symbols_count: int
    related_tests_count: int

    risk_level: str
    findings_count: int
    high_severity_findings_count: int


from sqlalchemy.orm import selectinload

@router.get("/{run_id}/summary", response_model=ReviewSummary)
async def get_review_summary(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReviewRun)
        .options(selectinload(ReviewRun.pull_request).selectinload(PullRequest.project))
        .filter_by(id=run_id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Review run not found")
        
    return ReviewSummary(
        review_id=str(job.id),
        status=job.status,
        repository=job.pull_request.project.name,
        pull_request_number=job.pull_request.pr_number,
        changed_files_count=job.changed_files_count or 0,
        changed_lines_count=job.changed_lines_count or 0,
        changed_symbols_count=job.changed_symbols_count or 0,
        affected_files_count=job.affected_files_count or 0,
        affected_symbols_count=job.affected_symbols_count or 0,
        related_tests_count=job.related_tests_count or 0,
        risk_level=job.risk_level or "medium",
        findings_count=job.findings_count or 0,
        high_severity_findings_count=job.high_severity_findings_count or 0
    )


@router.get("/{run_id}/symbols")
async def get_review_symbols(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReviewRun).filter_by(id=run_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Review run not found")
        
    if not job.impact_graph_data:
        return {"changed_symbols": []}
        
    symbols = job.impact_graph_data.get("changed_symbols", [])
    return {"changed_symbols": symbols}

