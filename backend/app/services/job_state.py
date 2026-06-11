from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.models import AudioFile, ProcessingJob


ALLOWED_JOB_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"running", "cancelled", "failed"},
    "running": {"completed", "failed", "cancelled"},
    "failed": {"queued"},
    "completed": set(),
    "cancelled": set(),
}


def transition_job(db: Session, job: ProcessingJob, next_status: str, error_message: str | None = None) -> ProcessingJob:
    allowed = ALLOWED_JOB_TRANSITIONS.get(job.status, set())
    if next_status not in allowed and next_status != job.status:
        raise ValueError(f"Invalid processing job transition: {job.status} -> {next_status}")

    job.status = next_status
    job.error_message = error_message
    if next_status == "running" and job.started_at is None:
        job.started_at = datetime.now(UTC)
    if next_status in {"completed", "failed", "cancelled"}:
        job.completed_at = datetime.now(UTC)
    db.flush()
    return job


def sync_audio_status(audio_file: AudioFile, job_status: str) -> None:
    status_map = {
        "queued": "queued",
        "running": "processing",
        "completed": "processed",
        "failed": "failed",
        "cancelled": "failed",
    }
    audio_file.status = status_map[job_status]

