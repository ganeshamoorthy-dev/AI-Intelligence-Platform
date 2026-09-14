from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# engine is equivalent to a JDBC DataSource in Java. It manages connection pooling.
engine = create_async_engine(settings.async_database_uri, echo=False)

# async_session_maker acts like a SessionFactory in Hibernate. It spawns new sessions.
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Provider for Database Sessions.
    
    Spring Boot Analogy: In Spring, you usually inject an EntityManager or rely on 
    the @Transactional annotation to manage session boundaries. 
    In FastAPI, this generator function yields a DB session and safely closes it 
    after the HTTP request finishes. This is injected into the controller (router) using `Depends(get_db)`.
    """
    async with async_session_maker() as session:
        yield session
