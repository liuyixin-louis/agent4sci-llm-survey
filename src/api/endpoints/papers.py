"""
Paper upload and management endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime
from pathlib import Path

from src.api.models.base import Paper, PaperListResponse, PaperUpload

router = APIRouter()

# In-memory storage for demo (would use database in production)
papers_db = {}


@router.post("/upload")
async def upload_papers(
    files: List[UploadFile] = File(default=[]),
    upload_request: Optional[PaperUpload] = None
):
    """Upload PDF files or URLs for processing."""
    session_id = str(uuid.uuid4())
    uploaded_papers = []
    
    # Handle file uploads
    for file in files:
        if file.filename.endswith('.pdf'):
            paper_id = str(uuid.uuid4())
            
            # Create upload directory
            upload_dir = Path(f"uploads/{session_id}")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file (simplified - would extract metadata in production)
            file_path = upload_dir / file.filename
            
            paper = Paper(
                id=paper_id,
                session_id=session_id,
                filename=file.filename,
                title=file.filename.replace('.pdf', ''),
                authors=[],
                abstract="Abstract would be extracted from PDF",
                upload_time=datetime.utcnow(),
                file_path=str(file_path)
            )
            
            papers_db[paper_id] = paper
            uploaded_papers.append(paper)
    
    # Handle URL uploads if provided
    if upload_request and upload_request.urls:
        for url in upload_request.urls:
            paper_id = str(uuid.uuid4())
            paper = Paper(
                id=paper_id,
                session_id=session_id,
                title=f"Paper from {url}",
                authors=[],
                abstract="Would fetch and extract from URL",
                upload_time=datetime.utcnow(),
                url=url
            )
            papers_db[paper_id] = paper
            uploaded_papers.append(paper)
    
    return {
        "session_id": session_id,
        "papers_uploaded": len(uploaded_papers),
        "papers": uploaded_papers
    }


@router.get("/", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = None
):
    """List uploaded papers with pagination."""
    # Filter by session if provided
    filtered_papers = list(papers_db.values())
    if session_id:
        filtered_papers = [p for p in filtered_papers if p.session_id == session_id]
    
    # Pagination
    total = len(filtered_papers)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaperListResponse(
        total_count=total,
        current_page=page,
        page_size=page_size,
        papers=filtered_papers[start:end]
    )


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get detailed paper information."""
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return papers_db[paper_id]