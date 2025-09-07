"""
Health check endpoint
"""

from fastapi import APIRouter
from datetime import datetime

from src.api.models.base import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        service="Survey Generation API",
        version="1.0.0"
    )