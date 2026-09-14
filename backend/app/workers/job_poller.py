import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.repositories.job_repo import JobRepository
from app.services.review.orchestrator import ReviewService

logger = logging.getLogger(__name__)

async def process_job(job, session: AsyncSession):
    """
    Executes the actual business logic for a job.
    
    Spring Boot Analogy: This is equivalent to an `@Async` method in a `@Service` class 
    that runs the heavy lifting in a background thread pool.
    """
    logger.info(f"Processing job {job.id} for PR {job.pull_request_id}")
    from datetime import datetime, timezone
    job.started_at = datetime.now(timezone.utc)
    await session.commit()
    try:
        # Load relationships required by the pipeline (mocking this conceptually)
        # We assume job.pull_request.project is available (requires eager loading in repo)
        
        review_service = ReviewService(session)
        publish_success = await review_service.execute_review(job)
        
        job.status = "completed" if publish_success else "completed_publish_failed"
    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        job.status = "failed"
        job.error_message = str(e)
    finally:
        job.completed_at = datetime.now(timezone.utc)
        if job.started_at:
            job.latency_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
            logger.info(f"Job {job.id} completed in {job.latency_ms}ms with status {job.status}. Total tokens: {job.total_tokens}")
        else:
            logger.warning(f"Job {job.id} has no started_at time!")
    
    # Equivalent to returning from a @Transactional method
    await session.commit()
    logger.info(f"Committed final state for Job {job.id}")

async def start_polling():
    """
    Continuous background polling loop.
    
    Spring Boot Analogy: This loop replaces the need for Quartz or `@Scheduled(fixedDelay = 5000)`.
    Since Python `asyncio` is highly efficient, a simple `while True` with `await asyncio.sleep(5)` 
    is a standard, lightweight pattern for a background daemon.
    """
    engine = create_async_engine(settings.async_database_uri, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    logger.info("Starting background polling worker...")
    while True:
        try:
            async with async_session() as session:
                job_repo = JobRepository(session)
                job = await job_repo.get_pending_job()
                if job:
                    await process_job(job, session)
                else:
                    await asyncio.sleep(5) # Sleep if no jobs
        except Exception as e:
            logger.error(f"Worker encountered an error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_polling())
