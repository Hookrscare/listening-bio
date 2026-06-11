from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.session import get_db
from backend.app.models import AudioFile, Detection, Organization, ProcessingJob, Project, RawModelOutput, Report, Site
from backend.app.schemas.api import (
    AudioFileCreate,
    AudioFileRead,
    DetectionRead,
    OrganizationRead,
    ProcessingJobCreate,
    ProcessingJobRead,
    ProjectRead,
    ProjectSummary,
    RawModelOutputRead,
    ReportCreate,
    ReportRead,
    SiteRead,
)
from backend.app.services.mock_processing import ensure_processing_job
from backend.app.services.summaries import get_project_summary
from backend.app.workers.processing_worker import run_job_once

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)) -> list[Organization]:
    return list(db.scalars(select(Organization).order_by(Organization.name)))


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.name)))


@router.get("/projects/{project_id}/summary", response_model=ProjectSummary)
def project_summary(project_id: str, db: Session = Depends(get_db)) -> ProjectSummary:
    summary = get_project_summary(db, project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return summary


@router.get("/sites", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)) -> list[Site]:
    return list(db.scalars(select(Site).order_by(Site.name)))


@router.post("/audio-files", response_model=AudioFileRead, status_code=201)
def create_audio_file(payload: AudioFileCreate, db: Session = Depends(get_db)) -> AudioFile:
    site = db.get(Site, payload.site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found.")

    if payload.idempotency_key:
        existing = db.scalar(
            select(AudioFile).where(
                AudioFile.site_id == payload.site_id,
                AudioFile.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            return existing

    audio_file = AudioFile(**payload.model_dump(), status="uploaded")
    db.add(audio_file)
    db.flush()
    ensure_processing_job(db, audio_file)
    db.refresh(audio_file)
    return audio_file


@router.get("/audio-files", response_model=list[AudioFileRead])
def list_audio_files(db: Session = Depends(get_db)) -> list[AudioFile]:
    return list(db.scalars(select(AudioFile).order_by(AudioFile.created_at.desc())))


@router.post("/processing-jobs", response_model=ProcessingJobRead, status_code=201)
def create_processing_job(payload: ProcessingJobCreate, db: Session = Depends(get_db)) -> ProcessingJob:
    audio_file = db.get(AudioFile, payload.audio_file_id)
    if audio_file is None:
        raise HTTPException(status_code=404, detail="Audio file not found.")
    job = ProcessingJob(audio_file_id=payload.audio_file_id, job_type=payload.job_type)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/processing-jobs", response_model=list[ProcessingJobRead])
def list_processing_jobs(db: Session = Depends(get_db)) -> list[ProcessingJob]:
    return list(db.scalars(select(ProcessingJob).order_by(ProcessingJob.created_at.desc())))


@router.post("/processing-jobs/{job_id}/run-mock", response_model=ProcessingJobRead)
def run_processing_job(job_id: str, db: Session = Depends(get_db)) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    if job.status == "completed":
        return job
    try:
        return run_job_once(db, job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/detections", response_model=list[DetectionRead])
def list_detections(db: Session = Depends(get_db)) -> list[Detection]:
    return list(db.scalars(select(Detection).order_by(Detection.created_at.desc())))


@router.get("/raw-model-outputs", response_model=list[RawModelOutputRead])
def list_raw_model_outputs(db: Session = Depends(get_db)) -> list[RawModelOutput]:
    return list(db.scalars(select(RawModelOutput).order_by(RawModelOutput.created_at.desc())))


@router.post("/reports", response_model=ReportRead, status_code=201)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)) -> Report:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    report = Report(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports", response_model=list[ReportRead])
def list_reports(db: Session = Depends(get_db)) -> list[Report]:
    return list(db.scalars(select(Report).order_by(Report.created_at.desc())))
