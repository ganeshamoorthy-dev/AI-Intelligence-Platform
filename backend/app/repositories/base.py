from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Base

# ModelType acts like a generic type parameter <T> in Java.
# We bound it to `Base` to ensure the repository only deals with valid SQLAlchemy entities.
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base Repository Pattern Implementation.
    
    Spring Boot Analogy: This is equivalent to Spring Data JPA's `JpaRepository<T, ID>` or 
    `CrudRepository<T, ID>`. It abstracts away the raw SQL/Session interactions, 
    providing a clean interface for data access.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Constructor. 
        In Python, `__init__` is like a class constructor in Java.
        We pass the SQLAlchemy `AsyncSession` which acts similarly to the JPA `EntityManager`.
        """
        self.model = model
        self.session = session

    async def get(self, id: Any) -> Optional[ModelType]:
        """
        Retrieves a single entity by its primary key.
        Spring Boot Analogy: `findById(id)`
        """
        result = await self.session.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Retrieves a paginated list of entities.
        Spring Boot Analogy: `findAll(PageRequest.of(page, size))`
        """
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, *, obj_in: dict) -> ModelType:
        """
        Creates and persists a new entity.
        Spring Boot Analogy: `save(entity)` (when inserting a new record)
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        Updates an existing entity with new values.
        Spring Boot Analogy: `save(entity)` (when updating an existing record)
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: Any) -> ModelType:
        """
        Deletes an entity by its primary key.
        Spring Boot Analogy: `deleteById(id)`
        """
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
        return obj
