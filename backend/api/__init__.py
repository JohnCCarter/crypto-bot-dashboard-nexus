"""
API routes module for FastAPI.
"""

from fastapi import APIRouter
from backend.api.status import router as status_router
from backend.api.balances import router as balances_router

# Create API router
api_router = APIRouter()

# Routers will be included after they are created
# Example: api_router.include_router(status_router)

# Include all routers
api_router.include_router(status_router)
api_router.include_router(balances_router) 