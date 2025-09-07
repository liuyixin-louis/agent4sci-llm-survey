"""
FastAPI application for Survey Generation API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers
from src.api.endpoints import papers, surveys, websocket, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Survey Generation API...")
    # Startup code here
    yield
    # Shutdown code here
    logger.info("Shutting down Survey Generation API...")


# Create FastAPI app
app = FastAPI(
    title="Survey Generation API",
    description="API for generating scientific surveys using LLM-based systems",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if os.getenv("DEBUG") == "true" else "An unexpected error occurred",
            "path": str(request.url)
        }
    )


# Include routers
app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])
app.include_router(surveys.router, prefix="/api/v1/surveys", tags=["surveys"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Survey Generation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG") == "true"
    )