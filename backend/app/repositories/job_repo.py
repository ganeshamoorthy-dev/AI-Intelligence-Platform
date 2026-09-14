from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.db.models import ReviewRun, PullRequest, Project

class JobRepository(BaseRepository[ReviewRun]):
    """
    Concrete Repository for ReviewRun entities.
    
    Spring Boot Analogy: This is equivalent to extending `JpaRepository<ReviewRun, Long>`
    and adding custom `@Query` methods.
    """
    def __init__(self, session: AsyncSession):
        super().__init__(ReviewRun, session)
        
    async def get_pending_job(self) -> ReviewRun | None:
        """
        Atomically fetch a pending job and mark it as processing using FOR UPDATE SKIP LOCKED.
        
        Spring Boot Analogy: This is equivalent to a custom `@Query` with 
        `@Lock(LockModeType.PESSIMISTIC_WRITE)` combined with native PostgreSQL `SKIP LOCKED` 
        to ensure multiple workers don't grab the same job.
        """
        result = await self.session.execute(
            select(self.model)
            .options(
                selectinload(self.model.pull_request)
                .selectinload(PullRequest.project)
                .selectinload(Project.scm_account)
            )
            .where(self.model.status == "pending")
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        job = result.scalars().first()
        if job:
            job.status = "processing"
            await self.session.commit()
            await self.session.refresh(job)
        return job
