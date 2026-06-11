from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.session import get_db
from backend.app.models import AudioFile, Detection, Organization, ProcessingJob, Project, RawModelOutput, Report, Site
from backend.app.schemas.api import (
    AudioFileCreate,
    AudioFileRead,
    DetectionRead,
    DetectionUpdate,
    OrganizationRead,
    ProcessingJobCreate,
    ProcessingJobRead,
    ProjectCreate,
    ProjectDashboard,
    ProjectRead,
    ProjectSummary,
    RawModelOutputRead,
    ReportCreate,
    ReportRead,
    SiteCreate,
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


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    organization = db.get(Organization, payload.organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    if payload.status not in {"active", "paused", "archived"}:
        raise HTTPException(status_code=400, detail="Invalid project status.")
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.get("/projects/{project_id}/summary", response_model=ProjectSummary)
def project_summary(project_id: str, db: Session = Depends(get_db)) -> ProjectSummary:
    summary = get_project_summary(db, project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return summary


@router.get("/projects/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard(project_id: str, db: Session = Depends(get_db)) -> ProjectDashboard:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    summary = get_project_summary(db, project_id)
    sites = list(db.scalars(select(Site).where(Site.project_id == project_id).order_by(Site.name)))
    recent_audio_files = list(
        db.scalars(
            select(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id)
            .order_by(AudioFile.created_at.desc())
            .limit(8)
        )
    )
    recent_detections = list(
        db.scalars(
            select(Detection)
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id)
            .order_by(Detection.created_at.desc())
            .limit(10)
        )
    )
    job_rows = db.execute(
        select(ProcessingJob.status, func.count(ProcessingJob.id))
        .join(AudioFile)
        .join(Site)
        .where(Site.project_id == project_id)
        .group_by(ProcessingJob.status)
    ).all()
    species_rows = db.execute(
        select(Detection.label, func.count(Detection.id))
        .join(AudioFile)
        .join(Site)
        .where(Site.project_id == project_id, Detection.detection_type == "species")
        .group_by(Detection.label)
        .order_by(func.count(Detection.id).desc())
        .limit(5)
    ).all()
    return ProjectDashboard(
        project=project,
        summary=summary,
        sites=sites,
        recent_audio_files=recent_audio_files,
        recent_detections=recent_detections,
        job_counts_by_status={status: count for status, count in job_rows},
        top_species=[{"label": label, "count": count} for label, count in species_rows],
    )


@router.get("/sites", response_model=list[SiteRead])
def list_sites(project_id: str | None = None, db: Session = Depends(get_db)) -> list[Site]:
    query = select(Site)
    if project_id:
        query = query.where(Site.project_id == project_id)
    return list(db.scalars(query.order_by(Site.name)))


@router.post("/sites", response_model=SiteRead, status_code=201)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)) -> Site:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    site = Site(**payload.model_dump())
    if site.latitude is not None and site.longitude is not None:
        site.location_geom_wkt = f"POINT({site.longitude} {site.latitude})"
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/sites/{site_id}", response_model=SiteRead)
def get_site(site_id: str, db: Session = Depends(get_db)) -> Site:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found.")
    return site


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
def list_audio_files(
    site_id: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[AudioFile]:
    query = select(AudioFile)
    if project_id:
        query = query.join(Site).where(Site.project_id == project_id)
    if site_id:
        query = query.where(AudioFile.site_id == site_id)
    if status:
        query = query.where(AudioFile.status == status)
    return list(db.scalars(query.order_by(AudioFile.created_at.desc())))


@router.get("/audio-files/{audio_file_id}", response_model=AudioFileRead)
def get_audio_file(audio_file_id: str, db: Session = Depends(get_db)) -> AudioFile:
    audio_file = db.get(AudioFile, audio_file_id)
    if audio_file is None:
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return audio_file


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
def list_processing_jobs(
    audio_file_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProcessingJob]:
    query = select(ProcessingJob)
    if audio_file_id:
        query = query.where(ProcessingJob.audio_file_id == audio_file_id)
    if status:
        query = query.where(ProcessingJob.status == status)
    return list(db.scalars(query.order_by(ProcessingJob.created_at.desc())))


@router.get("/processing-jobs/{job_id}", response_model=ProcessingJobRead)
def get_processing_job(job_id: str, db: Session = Depends(get_db)) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    return job


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
def list_detections(
    audio_file_id: str | None = None,
    project_id: str | None = None,
    detection_type: str | None = Query(default=None, pattern="^(species|sound_class)$"),
    db: Session = Depends(get_db),
) -> list[Detection]:
    query = select(Detection)
    if project_id:
        query = query.join(AudioFile).join(Site).where(Site.project_id == project_id)
    if audio_file_id:
        query = query.where(Detection.audio_file_id == audio_file_id)
    if detection_type:
        query = query.where(Detection.detection_type == detection_type)
    return list(db.scalars(query.order_by(Detection.created_at.desc())))


@router.get("/detections/{detection_id}", response_model=DetectionRead)
def get_detection(detection_id: str, db: Session = Depends(get_db)) -> Detection:
    detection = db.get(Detection, detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found.")
    return detection


@router.patch("/detections/{detection_id}", response_model=DetectionRead)
def update_detection(detection_id: str, payload: DetectionUpdate, db: Session = Depends(get_db)) -> Detection:
    detection = db.get(Detection, detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found.")
    if payload.review_status not in {"unreviewed", "confirmed", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid review status.")
    detection.review_status = payload.review_status
    db.commit()
    db.refresh(detection)
    return detection


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


@router.get("/reports/{report_id}", response_model=ReportRead)
def get_report(report_id: str, db: Session = Depends(get_db)) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
