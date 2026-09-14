from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.db.session import get_db
from app.db.models import Project, ReviewRun, ReviewFinding, PullRequest

router = APIRouter()

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Returns high-level dashboard KPIs.
    """
    # Note: Using count() for simplicity, in a real app you might use specialized metrics queries.
    total_projects = await db.scalar(select(func.count()).select_from(Project))
    active_jobs = await db.scalar(select(func.count()).select_from(ReviewRun).where(ReviewRun.status.in_(["pending", "processing"])))
    total_issues = await db.scalar(select(func.count()).select_from(ReviewFinding))
    
    # Calculate real average latency
    completed_jobs = await db.execute(
        select(ReviewRun.started_at, ReviewRun.completed_at)
        .where(ReviewRun.status.in_(["completed", "completed_publish_failed"]))
        .where(ReviewRun.started_at.is_not(None))
        .where(ReviewRun.completed_at.is_not(None))
    )
    
    latencies = [
        (row.completed_at - row.started_at).total_seconds() * 1000 
        for row in completed_jobs.all()
    ]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    total_tokens = await db.scalar(select(func.sum(ReviewRun.total_tokens)))
    
    return {
        "total_projects": total_projects or 0,
        "active_jobs": active_jobs or 0,
        "total_issues_found": total_issues or 0,
        "avg_latency_ms": int(avg_latency),
        "total_tokens_used": total_tokens or 0
    }

@router.get("/jobs")
async def get_recent_jobs(db: AsyncSession = Depends(get_db)):
    """
    Returns a list of the most recent ReviewRuns with Project and PR context.
    """
    result = await db.execute(
        select(ReviewRun, PullRequest, Project)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Project, PullRequest.project_id == Project.id)
        .order_by(ReviewRun.id.desc())
        .limit(10)
    )
    rows = result.all()
    return [
        {
            "id": row.ReviewRun.id,
            "repo_name": row.Project.name,
            "pr_number": row.PullRequest.pr_number,
            "pr_title": row.PullRequest.title,
            "status": row.ReviewRun.status,
            "commit_sha": row.ReviewRun.commit_sha,
            "started_at": row.ReviewRun.started_at,
            "completed_at": row.ReviewRun.completed_at,
            "latency_ms": row.ReviewRun.latency_ms,
            "total_tokens": row.ReviewRun.total_tokens
        } for row in rows
    ]

@router.get("/jobs/{job_id}/findings")
async def get_job_findings(job_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns the ReviewFindings, PR details, and Graph for a specific ReviewRun.
    """
    from fastapi import HTTPException
    from sqlalchemy.orm import selectinload
    
    # Load run, PR, and Project together
    result = await db.execute(
        select(ReviewRun, PullRequest, Project)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Project, PullRequest.project_id == Project.id)
        .options(selectinload(Project.scm_account))
        .where(ReviewRun.id == job_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    run = row.ReviewRun
    pr = row.PullRequest
    project = row.Project

    result = await db.execute(
        select(ReviewFinding).where(ReviewFinding.review_run_id == job_id)
    )
    findings = result.scalars().all()
    
    return {
        "pr_metadata": {
            "title": pr.title,
            "number": pr.pr_number,
            "author": pr.author,
            "repo_name": project.name,
            "status": run.status,
            "commit_sha": run.commit_sha,
            "scm_account_name": project.scm_account.name if project.scm_account else "Unknown",
            "scm_provider": project.scm_provider,
            "latency_ms": run.latency_ms,
            "total_tokens": run.total_tokens,
            "input_tokens": run.input_tokens,
            "output_tokens": run.output_tokens
        },
        "blast_radius_summary": run.blast_radius_summary,
        "impact_graph_data": run.impact_graph_data,
        "diff_data": run.diff_data,
        "findings": [
            {
                "id": f.id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
                "category": f.category,
                "description": f.description,
                "suggested_fix": f.suggested_fix
            } for f in findings
        ]
    }
