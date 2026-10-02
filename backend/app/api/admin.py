from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db, engine
from app.db.models import Base

logger = logging.getLogger(__name__)

router = APIRouter()

@router.delete("/reset-db")
async def reset_database(
    deleteTables: bool = Query(False, alias="deleteTables"),
    db: AsyncSession = Depends(get_db)
):
    """
    Cleans up all data in the database.
    If deleteTables is true, drops all tables entirely.
    """
    try:
        if deleteTables:
            logger.warning("Dropping all tables...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            # Recreate tables immediately so the app doesn't crash on next request
            logger.info("Recreating tables...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            return {"status": "success", "message": "All tables dropped and recreated."}
        else:
            logger.warning("Deleting all rows from all tables...")
            # We must delete in reverse dependency order, but SQLAlchemy metadata drop handles it safely.
            # For data deletion, we can just execute DELETE statements for all tables.
            for table in reversed(Base.metadata.sorted_tables):
                await db.execute(table.delete())
            
            await db.commit()
            return {"status": "success", "message": "All data cleared from tables."}
            
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {str(e)}")
