"""
Status API endpoints.
"""

import os
from typing import Any, Dict

from fastapi import APIRouter

from backend.api.models import HealthResponse, StatusResponse

# Create router
router = APIRouter(
    prefix="/api",
    tags=["status"],
)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/status", response_model=StatusResponse)
async def api_status() -> Dict[str, Any]:
    """Status endpoint, returns system status."""
    return {
        "status": "operational",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
