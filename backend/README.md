# AI Developer Intelligence Platform - Backend Architecture

Welcome to the backend of the AI Developer Intelligence Platform! 

Since you are transitioning from **Java Spring Boot**, this guide translates Python/FastAPI concepts into terms and patterns you are already familiar with.

## Architecture Mapping: Spring Boot vs FastAPI

The backend follows a strict **Clean Architecture** (layered architecture).

| Concept | Java Spring Boot | Python FastAPI |
| :--- | :--- | :--- |
| **Framework** | Spring Boot (Tomcat, Blocking/Reactive) | FastAPI (Starlette/Uvicorn, Asynchronous) |
| **Controllers** | `@RestController`, `@RequestMapping` | `APIRouter()`, `@router.post("/path")` |
| **Dependency Injection** | `@Autowired`, `@Bean`, ApplicationContext | `Depends()`, explicit parameter passing |
| **Data Validation/DTOs**| Record Classes, `@Valid`, Jackson | Pydantic Models (`BaseModel`) |
| **ORM Framework** | Hibernate / JPA | SQLAlchemy 2.0 |
| **Entity Mapping** | `@Entity`, `@Id`, `@Column` | `DeclarativeBase`, `Mapped`, `mapped_column` |
| **Data Access Layer** | `JpaRepository<T, ID>` | `BaseRepository` (Generic Custom Class) |
| **Database Migrations** | Flyway / Liquibase | Alembic |
| **Background Tasks** | `@Scheduled`, `@Async`, Quartz | `asyncio` loops, Celery (removed here for native poller) |

---

## Directory Structure

```text
backend/
├── app/
│   ├── api/            # Controllers (FastAPI Routers handling HTTP requests)
│   ├── core/           # Configuration (application.properties equivalent)
│   ├── db/             # Database connection setup (DataSource / EntityManager setup)
│   ├── models/         # SQLAlchemy Entities (JPA @Entity classes)
│   ├── schemas/        # Pydantic DTOs (Request/Response payload structures)
│   ├── repositories/   # Data Access Layer (Spring Data Repositories)
│   ├── services/       # Business Logic Layer (@Service classes)
│   ├── workers/        # Background polling processes (@Scheduled tasks)
│   └── utils/          # Helper functions
```

---

## Core Technologies Explained

### 1. FastAPI (The Controller Layer)
In Spring Boot, you use `@RestController`. In FastAPI, you create an `APIRouter` and use decorators like `@router.post(...)`. FastAPI automatically parses JSON bodies into Python objects using Pydantic, similar to how Jackson deserializes JSON into Java objects.

### 2. Pydantic (The DTO Layer)
Pydantic is used for data validation. A Pydantic `BaseModel` guarantees that the incoming JSON payload matches the exact types you specified. It's equivalent to combining Java DTOs with `javax.validation` annotations (like `@NotNull`).

### 3. Dependency Injection (`Depends`)
Spring uses the IOC container and `@Autowired` to magically wire services and repositories together. FastAPI is more explicit. You declare dependencies directly in the endpoint signature using `Depends(dependency_function)`. FastAPI will execute the function and inject the result (e.g. providing a database session for every request).

### 4. SQLAlchemy 2.0 (The ORM Layer)
SQLAlchemy is the Python equivalent of Hibernate. In version 2.0, it uses Python type hints (`Mapped[str]`) to generate database schemas, similar to JPA's `@Column`. We use `asyncpg` to make database interactions fully asynchronous.

### 5. Repository Pattern
To keep the codebase decoupled, we don't query the database directly in the controller or service. Instead, we created a generic `BaseRepository` class that mimics `JpaRepository`'s `findById`, `save`, and `deleteById` methods.

---

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the API Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
### 4. Simulating a Webhook (Consuming the API)

To test the system locally without actual GitHub events, you can simulate a GitHub pull request event using `curl` (or Postman).

First, start your backend server (`uvicorn app.main:app --reload`). Then run this command in a new terminal:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "x-github-event: pull_request" \
  -d '{
    "action": "opened",
    "pull_request": {
      "number": 1,
      "title": "Test PR",
      "user": {"login": "testuser"},
      "head": {"sha": "abcdef123456"},
      "base": {"sha": "123456abcdef"}
    },
    "repository": {
      "full_name": "testuser/test-repo",
      "clone_url": "https://github.com/testuser/test-repo.git"
    }
  }'
```
*Note: Our current endpoint has HMAC signature verification (`x-hub-signature-256`), so if you send this raw payload, it will return a `401 Invalid HMAC signature`. To test locally, you can temporarily comment out lines 29-30 in `webhooks.py`.*
