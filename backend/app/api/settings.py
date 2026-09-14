from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models import PlatformSettings

logger = logging.getLogger(__name__)

router = APIRouter()

class SettingsResponse(BaseModel):
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    default_llm_model: str
    severity_threshold: str
    custom_instructions: Optional[str] = None

class SettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    default_llm_model: Optional[str] = None
    severity_threshold: Optional[str] = None
    custom_instructions: Optional[str] = None

@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSettings).limit(1))
    settings = result.scalars().first()
    
    if not settings:
        settings = PlatformSettings()
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        
    # Mask API keys for security in UI
    masked_openai = "sk-... (configured)" if settings.openai_api_key else ""
    masked_google = "AIza... (configured)" if settings.google_api_key else ""
    
    return {
        "openai_api_key": masked_openai,
        "google_api_key": masked_google,
        "default_llm_model": settings.default_llm_model,
        "severity_threshold": settings.severity_threshold,
        "custom_instructions": settings.custom_instructions
    }

@router.put("", response_model=SettingsResponse)
async def update_settings(update_data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformSettings).limit(1))
    settings = result.scalars().first()
    
    if not settings:
        settings = PlatformSettings()
        db.add(settings)
    
    if update_data.openai_api_key is not None:
        if update_data.openai_api_key == "":
            settings.openai_api_key = None
        elif not update_data.openai_api_key.endswith("(configured)"):
            settings.openai_api_key = update_data.openai_api_key
            
    if update_data.google_api_key is not None:
        if update_data.google_api_key == "":
            settings.google_api_key = None
        elif not update_data.google_api_key.endswith("(configured)"):
            settings.google_api_key = update_data.google_api_key
            
    if update_data.default_llm_model:
        settings.default_llm_model = update_data.default_llm_model
        
    if update_data.severity_threshold:
        settings.severity_threshold = update_data.severity_threshold
        
    if update_data.custom_instructions is not None:
        settings.custom_instructions = update_data.custom_instructions
        
    await db.commit()
    await db.refresh(settings)
    
    masked_openai = "sk-... (configured)" if settings.openai_api_key else ""
    masked_google = "AIza... (configured)" if settings.google_api_key else ""
    
    return {
        "openai_api_key": masked_openai,
        "google_api_key": masked_google,
        "default_llm_model": settings.default_llm_model,
        "severity_threshold": settings.severity_threshold,
        "custom_instructions": settings.custom_instructions
    }
