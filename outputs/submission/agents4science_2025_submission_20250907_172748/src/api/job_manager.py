"""
Job Manager for handling survey generation tasks
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPhase(Enum):
    """Job phase enumeration"""
    INITIALIZING = "initializing"
    LOADING_PAPERS = "loading_papers"
    GENERATING_OUTLINE = "generating_outline"
    WRITING_SECTIONS = "writing_sections"
    VERIFYING_QUALITY = "verifying_quality"
    IMPROVING_CONTENT = "improving_content"
    FINALIZING = "finalizing"


class JobManager:
    """Manages survey generation jobs"""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        """
        Initialize job manager
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent jobs
        """
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.job_queue: List[str] = []
        self.active_jobs: List[str] = []
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_history_file = Path("data/job_history.json")
        self._load_history()
    
    def create_job(
        self,
        job_id: str,
        topic: str,
        system_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new job
        
        Args:
            job_id: Unique job identifier
            topic: Survey topic
            system_type: System type (baseline, lce, iterative)
            **kwargs: Additional job parameters
            
        Returns:
            Job dictionary
        """
        job = {
            "job_id": job_id,
            "topic": topic,
            "system_type": system_type,
            "status": JobStatus.PENDING.value,
            "phase": JobPhase.INITIALIZING.value,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress": 0,
            "current_iteration": 0,
            "max_iterations": kwargs.get("max_iterations", 5),
            "quality_score": None,
            "estimated_time_remaining": None,
            "result": None,
            "error": None,
            "metadata": kwargs
        }
        
        self.jobs[job_id] = job
        self.job_queue.append(job_id)
        
        logger.info(f"Job created: {job_id} - {topic}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        **updates
    ) -> bool:
        """
        Update job status and attributes
        
        Args:
            job_id: Job identifier
            status: New status
            phase: New phase
            **updates: Additional updates
            
        Returns:
            True if successful
        """
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if status:
            job["status"] = status
            if status == JobStatus.PROCESSING.value and not job["started_at"]:
                job["started_at"] = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                job["completed_at"] = datetime.now().isoformat()
        
        if phase:
            job["phase"] = phase
            job["progress"] = self._calculate_progress(phase, job["current_iteration"], job["max_iterations"])
        
        # Apply additional updates
        for key, value in updates.items():
            job[key] = value
        
        # Estimate remaining time
        if job["started_at"] and job["progress"] > 0:
            job["estimated_time_remaining"] = self._estimate_time_remaining(job)
        
        logger.info(f"Job updated: {job_id} - Status: {status}, Phase: {phase}")
        return True
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if job["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
            return False
        
        job["status"] = JobStatus.CANCELLED.value
        job["completed_at"] = datetime.now().isoformat()
        
        # Remove from queues
        if job_id in self.job_queue:
            self.job_queue.remove(job_id)
        if job_id in self.active_jobs:
            self.active_jobs.remove(job_id)
        
        logger.info(f"Job cancelled: {job_id}")
        return True
    
    async def process_queue(self):
        """Process job queue"""
        while self.job_queue:
            if len(self.active_jobs) >= self.max_concurrent_jobs:
                await asyncio.sleep(1)
                continue
            
            job_id = self.job_queue.pop(0)
            self.active_jobs.append(job_id)
            
            # Start job processing (would be actual survey generation in production)
            asyncio.create_task(self._process_job(job_id))
    
    async def _process_job(self, job_id: str):
        """Process a single job (placeholder for actual implementation)"""
        try:
            # Update status
            self.update_job(job_id, status=JobStatus.PROCESSING.value)
            
            # Simulate processing phases
            phases = [
                JobPhase.LOADING_PAPERS,
                JobPhase.GENERATING_OUTLINE,
                JobPhase.WRITING_SECTIONS,
                JobPhase.VERIFYING_QUALITY,
                JobPhase.IMPROVING_CONTENT,
                JobPhase.FINALIZING
            ]
            
            for phase in phases:
                self.update_job(job_id, phase=phase.value)
                await asyncio.sleep(2)  # Simulate work
            
            # Complete job
            self.update_job(
                job_id,
                status=JobStatus.COMPLETED.value,
                quality_score=4.0,
                result={"title": "Generated Survey", "sections": []}
            )
            
        except Exception as e:
            logger.error(f"Job processing error: {e}")
            self.update_job(
                job_id,
                status=JobStatus.FAILED.value,
                error=str(e)
            )
        finally:
            if job_id in self.active_jobs:
                self.active_jobs.remove(job_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "total_jobs": len(self.jobs),
            "pending": len(self.job_queue),
            "active": len(self.active_jobs),
            "completed": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.COMPLETED.value),
            "failed": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.FAILED.value),
            "max_concurrent": self.max_concurrent_jobs
        }
    
    def _calculate_progress(self, phase: str, current_iteration: int, max_iterations: int) -> int:
        """Calculate job progress percentage"""
        phase_weights = {
            JobPhase.INITIALIZING.value: 5,
            JobPhase.LOADING_PAPERS.value: 10,
            JobPhase.GENERATING_OUTLINE.value: 20,
            JobPhase.WRITING_SECTIONS.value: 40,
            JobPhase.VERIFYING_QUALITY.value: 60,
            JobPhase.IMPROVING_CONTENT.value: 80,
            JobPhase.FINALIZING.value: 95
        }
        
        base_progress = phase_weights.get(phase, 0)
        
        # Add iteration progress for iterative systems
        if current_iteration > 0 and max_iterations > 0:
            iteration_progress = (current_iteration / max_iterations) * 20
            base_progress = min(base_progress + iteration_progress, 95)
        
        return int(base_progress)
    
    def _estimate_time_remaining(self, job: Dict[str, Any]) -> int:
        """Estimate time remaining in seconds"""
        if not job["started_at"] or job["progress"] == 0:
            return None
        
        started = datetime.fromisoformat(job["started_at"])
        elapsed = (datetime.now() - started).total_seconds()
        
        # Simple linear estimation
        if job["progress"] > 0:
            total_estimated = elapsed / (job["progress"] / 100)
            remaining = total_estimated - elapsed
            return max(0, int(remaining))
        
        return None
    
    def _load_history(self):
        """Load job history from file"""
        if self.job_history_file.exists():
            try:
                with open(self.job_history_file, "r") as f:
                    history = json.load(f)
                    # Only load completed/failed jobs
                    for job_id, job in history.items():
                        if job["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                            self.jobs[job_id] = job
            except Exception as e:
                logger.error(f"Failed to load job history: {e}")
    
    def save_history(self):
        """Save job history to file"""
        try:
            self.job_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.job_history_file, "w") as f:
                json.dump(self.jobs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save job history: {e}")
    
    def cleanup_old_jobs(self, days: int = 7):
        """Remove old completed/failed jobs"""
        cutoff = datetime.now() - timedelta(days=days)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if job["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                if job.get("completed_at"):
                    completed = datetime.fromisoformat(job["completed_at"])
                    if completed < cutoff:
                        jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
            self.save_history()


# Global job manager instance
job_manager = JobManager()