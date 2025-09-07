"""
Base Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SystemType(str, Enum):
    """Survey system types."""
    BASELINE = "baseline"
    LCE = "lce"
    ITERATIVE = "iterative"


class JobStatus(str, Enum):
    """Job status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PaperUpload(BaseModel):
    """Paper upload request model."""
    urls: Optional[List[str]] = Field(default=[], description="List of paper URLs")
    session_id: Optional[str] = Field(default=None, description="Session ID for grouping uploads")


class Paper(BaseModel):
    """Paper model."""
    id: str
    session_id: str
    filename: Optional[str] = None
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    upload_time: datetime
    file_path: Optional[str] = None
    url: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaperListResponse(BaseModel):
    """Paginated paper list response."""
    total_count: int
    current_page: int
    page_size: int
    papers: List[Paper]


class SurveyRequest(BaseModel):
    """Survey generation request model."""
    topic_name: str = Field(..., description="Topic for the survey")
    paper_ids: List[str] = Field(..., description="IDs of papers to include")
    system_type: SystemType = Field(default=SystemType.ITERATIVE, description="Survey system to use")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Maximum iterations for iterative system")
    model_preferences: Optional[Dict[str, Any]] = Field(default={}, description="Model configuration preferences")


class SurveyJob(BaseModel):
    """Survey generation job model."""
    survey_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_data: Optional[Dict[str, Any]] = {}
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SurveyStatus(BaseModel):
    """Survey generation status model."""
    survey_id: str
    status: JobStatus
    current_iteration: Optional[int] = None
    current_phase: Optional[str] = None
    quality_scores: Optional[Dict[str, float]] = None
    estimated_time_remaining: Optional[int] = None  # seconds
    progress_percentage: float = 0.0


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    path: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }