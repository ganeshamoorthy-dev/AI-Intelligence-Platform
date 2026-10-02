from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.db.models import ReviewRun, ReviewFinding, PullRequest, Project

router = APIRouter()

@router.get("/findings")
async def get_ide_findings(
    repo_url: str = Query(..., description="The repository URL, e.g. https://github.com/owner/repo"),
    branch: str = Query(None, description="The branch name"),
    commit_sha: str = Query(None, description="The specific commit SHA to fetch findings for"),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint dedicated for IDE plugins (VS Code, IntelliJ) to fetch AI code review findings
    for the currently checked out branch or commit.
    """
    if not branch and not commit_sha:
        raise HTTPException(status_code=400, detail="Must provide either branch or commit_sha")

    # 1. Find the project
    project_result = await db.execute(select(Project).where(Project.repository_url == repo_url))
    project = project_result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Find the most recent matching ReviewRun
    query = select(ReviewRun).join(PullRequest)
    
    if commit_sha:
        query = query.where(ReviewRun.commit_sha == commit_sha)
    elif branch:
        query = query.where(PullRequest.project_id == project.id).where(ReviewRun.status == "completed").order_by(ReviewRun.id.desc())
        
    run_result = await db.execute(query.limit(1))
    review_run = run_result.scalars().first()
    
    if not review_run:
        return {"findings": []}

    # 3. Fetch Findings
    findings_result = await db.execute(select(ReviewFinding).where(ReviewFinding.review_run_id == review_run.id))
    findings = findings_result.scalars().all()

    # 4. Format specifically for IDE consumption
    # IDEs need precise file paths, line numbers, and actionable fixes
    formatted = []
    for f in findings:
        formatted.append({
            "id": f.id,
            "file": f.file_path,
            "line": f.line_number,
            "severity": f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
            "message": f.description,
            "evidence": f.evidence,
            "why_it_matters": f.why_it_matters,
            "suggested_fix": f.suggested_fix,
            "confidence": f.confidence,
            "run_id": review_run.id,
            "created_at": f.created_at.isoformat()
        })

    return {
        "repo_url": repo_url,
        "commit_sha": review_run.commit_sha,
        "findings": formatted
    }
