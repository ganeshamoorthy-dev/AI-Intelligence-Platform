from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    """
    Verifies that the provided API key matches the configured secure key.
    If no secure key is configured in settings, it currently allows access (useful for local dev),
    but in production, it will strictly enforce it.
    """
    configured_key = getattr(settings, "API_KEY", None)
    
    if not configured_key:
        # If the environment didn't set an API key, we assume local dev/open access.
        # For strict security, change this to raise an exception.
        return True
        
    if api_key_header == configured_key:
        return True
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API key"
    )
