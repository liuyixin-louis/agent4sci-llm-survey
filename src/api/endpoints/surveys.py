"""
Survey generation endpoints
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
import uuid
from datetime import datetime

from src.api.models.base import SurveyRequest, SurveyJob, SurveyStatus, JobStatus

router = APIRouter()

# In-memory job storage
jobs_db = {}


async def generate_survey_task(survey_id: str, request: SurveyRequest):
    """Background task for survey generation."""
    # This would integrate with the actual survey generation system
    job = jobs_db[survey_id]
    job.status = JobStatus.RUNNING
    job.started_at = datetime.utcnow()
    
    # Simulate survey generation
    # In production, would call actual survey system
    
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    job.result_path = f"surveys/{survey_id}.json"


@router.post("/")
async def create_survey(
    request: SurveyRequest,
    background_tasks: BackgroundTasks
):
    """Trigger survey generation."""
    survey_id = str(uuid.uuid4())
    
    job = SurveyJob(
        survey_id=survey_id,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    jobs_db[survey_id] = job
    
    # Add to background tasks
    background_tasks.add_task(generate_survey_task, survey_id, request)
    
    return {
        "survey_id": survey_id,
        "status": "pending",
        "message": "Survey generation started"
    }


@router.get("/{survey_id}/status", response_model=SurveyStatus)
async def get_survey_status(survey_id: str):
    """Get survey generation status."""
    if survey_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    job = jobs_db[survey_id]
    
    return SurveyStatus(
        survey_id=survey_id,
        status=job.status,
        current_iteration=1,
        current_phase="Generation",
        progress_percentage=50.0 if job.status == JobStatus.RUNNING else 100.0
    )


@router.get("/{survey_id}")
async def get_survey(survey_id: str, format: str = "json"):
    """Get completed survey."""
    if survey_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    job = jobs_db[survey_id]
    
    if job.status != JobStatus.COMPLETED:
        return {
            "survey_id": survey_id,
            "status": job.status,
            "message": "Survey generation in progress"
        }
    
    # Return mock survey data
    return {
        "survey_id": survey_id,
        "topic": "Sample Survey",
        "sections": [
            {"title": "Introduction", "content": "Sample introduction"},
            {"title": "Conclusion", "content": "Sample conclusion"}
        ],
        "format": format
    }