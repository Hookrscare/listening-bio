from sqlalchemy.orm import Session

from backend.app.models import ProcessingJob
from backend.app.services.mock_processing import run_mock_processing


def run_job_once(db: Session, job: ProcessingJob) -> ProcessingJob:
    if job.job_type != "mock_audio_analysis":
        raise ValueError(f"Unsupported processing job type: {job.job_type}")
    return run_mock_processing(db, job)


def run_pending_jobs(db: Session, limit: int = 10) -> list[ProcessingJob]:
    jobs = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.status == "queued")
        .order_by(ProcessingJob.created_at.asc())
        .limit(limit)
        .all()
    )
    return [run_job_once(db, job) for job in jobs]

