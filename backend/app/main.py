from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx

from app.api.dashboard import router as dashboard_router
from app.api.reviews import router as reviews_router
from app.api.webhooks import router as webhooks_router
from app.api.github import router as github_router
from app.api.scm_accounts import router as scm_accounts_router
from app.api.settings import router as settings_router
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Event-driven, privacy-first system for context-aware pull request reviews",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Depends
from app.core.security import verify_api_key

app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"], dependencies=[Depends(verify_api_key)])
app.include_router(github_router, prefix="/api/v1/github", tags=["GitHub"], dependencies=[Depends(verify_api_key)])
app.include_router(reviews_router, prefix="/api/v1/reviews", tags=["Reviews"], dependencies=[Depends(verify_api_key)])
app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["Webhooks"]) # Webhooks often use their own HMAC signatures, so skip global API key here
app.include_router(scm_accounts_router, prefix="/api/v1/scm-accounts", tags=["SCM Accounts"], dependencies=[Depends(verify_api_key)])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"], dependencies=[Depends(verify_api_key)])

from app.api.ide import router as ide_router
from app.api.admin import router as admin_router
app.include_router(ide_router, prefix="/api/v1/ide", tags=["IDE Integration"], dependencies=[Depends(verify_api_key)])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"], dependencies=[Depends(verify_api_key)])

@app.get("/api/v1/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health_status = {
        "status": "ok",
        "api": "up",
        "database": "down",
        "llm": "down",
        "failing_services": []
    }
    
    # 1. Check PostgreSQL Database Connectivity
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "up"
    except Exception as e:
        health_status["status"] = "error"
        health_status["database"] = "down"
        health_status["failing_services"].append({"service": "database", "error": str(e)})
        
    # 2. Check Ollama LLM Connectivity
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/")
            if resp.status_code == 200:
                health_status["llm"] = "up"
            else:
                health_status["status"] = "error"
                health_status["llm"] = "down"
                health_status["failing_services"].append({"service": "llm", "error": f"HTTP {resp.status_code}"})
    except Exception as e:
        health_status["status"] = "error"
        health_status["llm"] = "down"
        health_status["failing_services"].append({"service": "llm", "error": str(e)})
        
    return health_status
