"""
FastAPI Web API for LLM Survey Generation
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.our_system.iterative import GlobalIterativeSystem
from src.baselines.autosurvey import AutoSurveyBaseline
from src.baselines.autosurvey_lce import AutoSurveyWithLCE
from src.data.data_loader import SciMCPDataLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Survey Generator API",
    description="REST API for automated scientific survey generation using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for active jobs and WebSocket connections
active_jobs: Dict[str, Dict] = {}
active_connections: Dict[str, List[WebSocket]] = {}

# Pydantic models
class PaperUpload(BaseModel):
    """Model for paper upload response"""
    paper_id: str
    filename: str
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    upload_time: datetime

class SurveyRequest(BaseModel):
    """Model for survey generation request"""
    topic: str = Field(..., description="Topic for the survey")
    paper_ids: Optional[List[str]] = Field(None, description="List of paper IDs to include")
    system_type: str = Field("iterative", description="System type: baseline, lce, or iterative")
    max_iterations: int = Field(5, description="Maximum iterations for iterative system")
    model_preference: str = Field("balanced", description="Model preference: fast, balanced, or complex")

class SurveyJob(BaseModel):
    """Model for survey job response"""
    survey_id: str
    status: str
    created_at: datetime
    topic: str
    system_type: str

class SurveyStatus(BaseModel):
    """Model for survey status response"""
    survey_id: str
    status: str
    current_iteration: Optional[int] = None
    current_phase: Optional[str] = None
    quality_score: Optional[float] = None
    estimated_time_remaining: Optional[int] = None
    error: Optional[str] = None

class Survey(BaseModel):
    """Model for completed survey"""
    survey_id: str
    title: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    quality_score: float
    iterations: int

# API key authentication
API_KEY = os.environ.get("API_KEY", "test-api-key-12345")

def verify_api_key(api_key: str):
    """Verify API key"""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LLM Survey Generator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/upload", response_model=PaperUpload)
@limiter.limit("30/minute")
async def upload_paper(
    request: Any,  # Required for rate limiting
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload a paper PDF or text file"""
    try:
        # Generate unique paper ID
        paper_id = str(uuid.uuid4())
        
        # Create upload directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{paper_id}_{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract metadata (simplified - in production would use PyPDF2)
        metadata = {
            "paper_id": paper_id,
            "filename": file.filename,
            "title": file.filename.replace(".pdf", "").replace("_", " ").title(),
            "authors": [],
            "abstract": None,
            "upload_time": datetime.now()
        }
        
        # Store metadata
        active_jobs[paper_id] = metadata
        
        logger.info(f"Paper uploaded: {paper_id} - {file.filename}")
        
        return PaperUpload(**metadata)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/surveys", response_model=SurveyJob)
@limiter.limit("10/minute")
async def create_survey(
    request: Any,  # Required for rate limiting
    survey_request: SurveyRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Create a new survey generation job"""
    try:
        # Generate survey ID
        survey_id = str(uuid.uuid4())
        
        # Create job entry
        job = {
            "survey_id": survey_id,
            "status": "pending",
            "created_at": datetime.now(),
            "topic": survey_request.topic,
            "system_type": survey_request.system_type,
            "paper_ids": survey_request.paper_ids,
            "max_iterations": survey_request.max_iterations,
            "model_preference": survey_request.model_preference,
            "current_iteration": 0,
            "current_phase": "initializing",
            "quality_score": None,
            "result": None,
            "error": None
        }
        
        active_jobs[survey_id] = job
        
        # Start background task
        background_tasks.add_task(
            generate_survey_task,
            survey_id,
            survey_request
        )
        
        logger.info(f"Survey job created: {survey_id} - {survey_request.topic}")
        
        return SurveyJob(
            survey_id=survey_id,
            status="pending",
            created_at=job["created_at"],
            topic=survey_request.topic,
            system_type=survey_request.system_type
        )
        
    except Exception as e:
        logger.error(f"Survey creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/surveys/{survey_id}/status", response_model=SurveyStatus)
async def get_survey_status(
    survey_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get status of a survey generation job"""
    if survey_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    job = active_jobs[survey_id]
    
    return SurveyStatus(
        survey_id=survey_id,
        status=job["status"],
        current_iteration=job.get("current_iteration"),
        current_phase=job.get("current_phase"),
        quality_score=job.get("quality_score"),
        estimated_time_remaining=job.get("estimated_time_remaining"),
        error=job.get("error")
    )

@app.get("/surveys/{survey_id}")
async def get_survey(
    survey_id: str,
    format: str = "json",
    api_key: str = Depends(verify_api_key)
):
    """Get completed survey"""
    if survey_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    job = active_jobs[survey_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Survey not ready. Status: {job['status']}"
        )
    
    result = job.get("result")
    if not result:
        raise HTTPException(status_code=500, detail="Survey result not available")
    
    if format == "json":
        return result
    elif format == "markdown":
        # Convert to markdown
        md = f"# {result['title']}\n\n"
        for section in result.get("sections", []):
            md += f"## {section.get('title', '')}\n\n"
            md += f"{section.get('content', '')}\n\n"
        return FileResponse(
            path=None,
            media_type="text/markdown",
            content=md.encode()
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@app.get("/papers")
async def list_papers(
    skip: int = 0,
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """List uploaded papers with pagination"""
    papers = []
    for paper_id, metadata in active_jobs.items():
        if "filename" in metadata:  # It's a paper upload
            papers.append(metadata)
    
    # Sort by upload time
    papers.sort(key=lambda x: x.get("upload_time", datetime.min), reverse=True)
    
    # Pagination
    total = len(papers)
    papers = papers[skip:skip + limit]
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "papers": papers
    }

@app.websocket("/ws/{survey_id}")
async def websocket_endpoint(websocket: WebSocket, survey_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    # Add connection to active connections
    if survey_id not in active_connections:
        active_connections[survey_id] = []
    active_connections[survey_id].append(websocket)
    
    try:
        # Keep connection alive and send updates
        while True:
            # Check if survey exists
            if survey_id in active_jobs:
                job = active_jobs[survey_id]
                update = {
                    "survey_id": survey_id,
                    "status": job["status"],
                    "current_iteration": job.get("current_iteration"),
                    "current_phase": job.get("current_phase"),
                    "quality_score": job.get("quality_score")
                }
                await websocket.send_json(update)
                
                # If completed or failed, close connection
                if job["status"] in ["completed", "failed"]:
                    break
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Remove connection
        if survey_id in active_connections:
            active_connections[survey_id].remove(websocket)

# Background task for survey generation
async def generate_survey_task(survey_id: str, request: SurveyRequest):
    """Background task to generate survey"""
    try:
        # Update status
        active_jobs[survey_id]["status"] = "processing"
        active_jobs[survey_id]["current_phase"] = "loading_papers"
        await broadcast_update(survey_id)
        
        # Load papers (simplified - in production would load actual papers)
        papers = []
        if request.paper_ids:
            # Load specific papers
            for paper_id in request.paper_ids:
                if paper_id in active_jobs:
                    papers.append({
                        "title": active_jobs[paper_id].get("title", "Unknown"),
                        "abstract": active_jobs[paper_id].get("abstract", "")
                    })
        else:
            # Use sample papers
            papers = [
                {"title": f"Paper {i}", "abstract": f"Abstract for paper {i}"}
                for i in range(10)
            ]
        
        # Select system
        if request.system_type == "iterative":
            system = GlobalIterativeSystem(max_iterations=request.max_iterations)
        elif request.system_type == "lce":
            system = AutoSurveyWithLCE()
        else:
            system = AutoSurveyBaseline()
        
        # Update phase
        active_jobs[survey_id]["current_phase"] = "generating_survey"
        await broadcast_update(survey_id)
        
        # Generate survey (simplified for demo)
        if request.system_type == "iterative":
            # Simulate iterative improvement
            for i in range(min(3, request.max_iterations)):
                active_jobs[survey_id]["current_iteration"] = i + 1
                active_jobs[survey_id]["current_phase"] = f"iteration_{i+1}"
                active_jobs[survey_id]["quality_score"] = 3.0 + (i * 0.5)
                await broadcast_update(survey_id)
                await asyncio.sleep(2)  # Simulate processing
            
            # Final result
            result = {
                "title": f"Survey on {request.topic}",
                "sections": [
                    {"title": "Introduction", "content": "Introduction content..."},
                    {"title": "Methods", "content": "Methods content..."},
                    {"title": "Results", "content": "Results content..."},
                    {"title": "Conclusion", "content": "Conclusion content..."}
                ],
                "quality_score": 4.0,
                "iterations": 3
            }
        else:
            # Simulate baseline generation
            await asyncio.sleep(5)
            result = {
                "title": f"Survey on {request.topic}",
                "sections": [
                    {"title": "Introduction", "content": "Basic introduction..."},
                    {"title": "Main Content", "content": "Main content..."},
                    {"title": "Conclusion", "content": "Basic conclusion..."}
                ],
                "quality_score": 3.5,
                "iterations": 1
            }
        
        # Update job with result
        active_jobs[survey_id]["status"] = "completed"
        active_jobs[survey_id]["result"] = result
        active_jobs[survey_id]["quality_score"] = result["quality_score"]
        await broadcast_update(survey_id)
        
        logger.info(f"Survey completed: {survey_id}")
        
    except Exception as e:
        logger.error(f"Survey generation error: {e}")
        active_jobs[survey_id]["status"] = "failed"
        active_jobs[survey_id]["error"] = str(e)
        await broadcast_update(survey_id)

async def broadcast_update(survey_id: str):
    """Broadcast update to WebSocket connections"""
    if survey_id in active_connections:
        job = active_jobs[survey_id]
        update = {
            "survey_id": survey_id,
            "status": job["status"],
            "current_iteration": job.get("current_iteration"),
            "current_phase": job.get("current_phase"),
            "quality_score": job.get("quality_score")
        }
        
        # Send to all connected clients
        for connection in active_connections[survey_id]:
            try:
                await connection.send_json(update)
            except:
                pass  # Connection might be closed

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_jobs": len(active_jobs),
        "active_connections": sum(len(conns) for conns in active_connections.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)