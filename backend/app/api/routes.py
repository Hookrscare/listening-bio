import csv
import json
from io import StringIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.api.deps import require_admin_key
from backend.app.db.session import get_db
from backend.app.models import AudioFile, Detection, Organization, ProcessingJob, Project, RawModelOutput, Report, Site
from backend.app.schemas.api import (
    AudioFileCreate,
    AudioFileRead,
    BiodiversityMetrics,
    BirdnetStatus,
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
from backend.app.services.audio_storage import save_uploaded_wav
from backend.app.services.birdnet_processing import birdnet_status
from backend.app.services.mock_processing import ensure_processing_job
from backend.app.services.summaries import get_biodiversity_metrics, get_evidence_provenance, get_project_summary
from backend.app.workers.processing_worker import run_job_once

router = APIRouter()


def _project_readiness_data(project_id: str, db: Session) -> dict[str, object]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    audio_rows = list(db.scalars(select(AudioFile).join(Site).where(Site.project_id == project_id)))
    detection_rows = list(db.scalars(select(Detection).join(AudioFile).join(Site).where(Site.project_id == project_id)))
    raw_rows = list(db.scalars(select(RawModelOutput).join(AudioFile).join(Site).where(Site.project_id == project_id)))
    site_count = db.scalar(select(func.count(Site.id)).where(Site.project_id == project_id)) or 0
    job_counts = {
        status: count
        for status, count in db.execute(
            select(ProcessingJob.status, func.count(ProcessingJob.id))
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id)
            .group_by(ProcessingJob.status)
        ).all()
    }

    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    review_counts = {
        status: sum(1 for detection in detection_rows if detection.review_status == status)
        for status in ("confirmed", "unreviewed", "rejected")
    }
    species_labels = {detection.label for detection in detection_rows if detection.detection_type == "species"}
    local_audio = sum(1 for audio in audio_rows if audio.storage_uri.startswith("file://"))
    simulated_audio = sum(1 for audio in audio_rows if audio.storage_uri.startswith("simulation://"))
    external_audio = len(audio_rows) - local_audio - simulated_audio

    readiness_checks = [
        {
            "label": "Project and mapped sites",
            "status": "complete" if site_count >= 3 else "incomplete",
            "detail": f"{site_count} site(s) configured",
        },
        {
            "label": "Audio survey effort",
            "status": "complete" if len(audio_rows) >= 50 else "partial" if audio_rows else "incomplete",
            "detail": f"{len(audio_rows)} recording record(s)",
        },
        {
            "label": "Model output provenance",
            "status": "complete" if raw_rows else "incomplete",
            "detail": f"{len(raw_rows)} raw model payload(s) retained",
        },
        {
            "label": "Real BirdNET inference",
            "status": "complete" if provenance.real_birdnet_outputs else "partial" if provenance.configured_no_detection_outputs else "incomplete",
            "detail": f"{provenance.real_birdnet_outputs} configured output(s), {provenance.simulated_outputs} simulated output(s)",
        },
        {
            "label": "Human review evidence",
            "status": "complete" if review_counts["confirmed"] >= 20 else "partial" if review_counts["confirmed"] else "incomplete",
            "detail": f"{review_counts['confirmed']} confirmed, {review_counts['rejected']} rejected",
        },
        {
            "label": "Export-ready detections",
            "status": "complete" if detection_rows else "incomplete",
            "detail": f"{len(detection_rows)} detection row(s)",
        },
    ]
    score_weights = {"complete": 1.0, "partial": 0.5, "incomplete": 0.0}
    readiness_score = round(
        sum(score_weights[check["status"]] for check in readiness_checks) / len(readiness_checks) * 100,
        1,
    )
    blockers = [check["label"] for check in readiness_checks if check["status"] != "complete"]

    return {
        "project_id": project.id,
        "project_name": project.name,
        "evidence_level": provenance.evidence_level,
        "readiness_score": readiness_score,
        "simulation_only": provenance.simulation_only,
        "can_make_ecological_claims": provenance.can_make_ecological_claims,
        "claim_status": provenance.claim_status,
        "disclaimer": provenance.disclaimer,
        "next_required_proof": provenance.next_required_proof,
        "counts": {
            "sites": site_count,
            "audio_files": len(audio_rows),
            "detections": len(detection_rows),
            "species_candidates": len(species_labels),
            "raw_model_outputs": len(raw_rows),
            "real_birdnet_outputs": provenance.real_birdnet_outputs,
            "configured_no_detection_outputs": provenance.configured_no_detection_outputs,
            "simulated_outputs": provenance.simulated_outputs,
            "local_audio_files": provenance.local_audio_files,
            "simulated_audio_files": provenance.simulated_audio_files,
            "external_audio_records": provenance.external_audio_records,
        },
        "review_counts": review_counts,
        "job_counts": job_counts,
        "checks": readiness_checks,
        "blockers": blockers,
        "message": (
            "Simulation rehearsal only; replace with approved field WAV recordings before making ecological claims."
            if provenance.simulation_only
            else "Real inference evidence is present; continue expanding field recordings and expert review."
            if provenance.real_birdnet_outputs
            else "Workflow is ready; configure BirdNET and upload real WAV recordings for ecological evidence."
        ),
    }


def _project_evidence_package(project_id: str, db: Session) -> dict[str, object]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    readiness = _project_readiness_data(project_id, db)
    summary = get_project_summary(db, project_id)
    metrics = get_biodiversity_metrics(db, project_id)
    site_rows = db.execute(
        select(
            Site.id,
            Site.name,
            Site.habitat_type,
            Site.latitude,
            Site.longitude,
            func.count(func.distinct(AudioFile.id)).label("audio_count"),
            func.count(Detection.id).label("detection_count"),
        )
        .outerjoin(AudioFile, AudioFile.site_id == Site.id)
        .outerjoin(Detection, Detection.audio_file_id == AudioFile.id)
        .where(Site.project_id == project_id)
        .group_by(Site.id, Site.name, Site.habitat_type, Site.latitude, Site.longitude)
        .order_by(Site.name)
    ).all()
    top_species = [
        {"label": label, "count": count}
        for label, count in db.execute(
            select(Detection.label, func.count(Detection.id))
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id, Detection.detection_type == "species")
            .group_by(Detection.label)
            .order_by(func.count(Detection.id).desc())
            .limit(10)
        ).all()
    ]
    recommendations = [
        "Replace simulated records with approved field WAV recordings."
        if readiness["simulation_only"]
        else "Expand the real recording dataset across repeated site visits.",
        "Run BirdNET with site coordinates, recording date, and documented confidence threshold.",
        "Review a representative detection sample with partner or trained reviewer input.",
        "Export detections, sites, and audio records before each partner review meeting.",
    ]
    if "Real BirdNET inference" in readiness["blockers"]:
        recommendations.insert(0, "Capture at least 50 real WAV recordings and run configured BirdNET inference.")

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
        },
        "readiness": readiness,
        "summary": summary.model_dump() if summary else None,
        "metrics": metrics.model_dump() if metrics else None,
        "sites": [
            {
                "id": site_id,
                "name": name,
                "habitat_type": habitat_type,
                "latitude": latitude,
                "longitude": longitude,
                "audio_count": audio_count,
                "detection_count": detection_count,
            }
            for site_id, name, habitat_type, latitude, longitude, audio_count, detection_count in site_rows
        ],
        "top_species": top_species,
        "recommendations": recommendations,
        "partner_language": (
            "This is a simulated pilot rehearsal, not a validated ecological result."
            if readiness["simulation_only"]
            else "This package includes real inference evidence and should still be reviewed before ecological claims."
        ),
        "disclaimer": "Prototype indicators only; not scientifically validated biodiversity scores.",
    }


def _evidence_markdown(package: dict[str, object]) -> str:
    readiness = package["readiness"]
    summary = package["summary"] or {}
    metrics = package["metrics"] or {}
    project = package["project"]
    lines = [
        f"# {project['name']} Evidence Package",
        "",
        f"Status: {project['status']}",
        f"Evidence level: {readiness['evidence_level']}",
        f"Readiness score: {readiness['readiness_score']}%",
        "",
        "## Important Disclaimer",
        str(package["disclaimer"]),
        str(package["partner_language"]),
        "",
        "## Summary",
        f"- Sites: {summary.get('site_count', 0)}",
        f"- Audio records: {summary.get('audio_file_count', 0)}",
        f"- Detections: {summary.get('detection_count', 0)}",
        f"- Candidate species richness: {summary.get('species_richness', 0)}",
        f"- Recording hours: {metrics.get('recording_hours', 0)}",
        f"- Confirmed detection percent: {metrics.get('confirmed_detection_percent', 0)}%",
        "",
        "## Readiness Checks",
    ]
    for check in readiness["checks"]:
        lines.append(f"- {check['status'].upper()}: {check['label']} — {check['detail']}")
    lines.extend(["", "## Top Species Candidates"])
    for item in package["top_species"]:
        lines.append(f"- {item['label']}: {item['count']}")
    lines.extend(["", "## Sites"])
    for site in package["sites"]:
        lines.append(f"- {site['name']} ({site['habitat_type']}): {site['audio_count']} audio, {site['detection_count']} detections")
    lines.extend(["", "## Recommended Next Actions"])
    for item in package["recommendations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/integrations/birdnet/status", response_model=BirdnetStatus)
def get_birdnet_status() -> dict[str, object]:
    return birdnet_status()


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)) -> list[Organization]:
    return list(db.scalars(select(Organization).order_by(Organization.name)))


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.name)))


@router.post("/projects", response_model=ProjectRead, status_code=201, dependencies=[Depends(require_admin_key)])
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


@router.get("/projects/{project_id}/metrics", response_model=BiodiversityMetrics)
def biodiversity_metrics(project_id: str, db: Session = Depends(get_db)) -> BiodiversityMetrics:
    metrics = get_biodiversity_metrics(db, project_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return metrics


@router.get("/projects/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard(project_id: str, db: Session = Depends(get_db)) -> ProjectDashboard:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    summary = get_project_summary(db, project_id)
    sites = list(db.scalars(select(Site).where(Site.project_id == project_id).order_by(Site.name)))
    provenance = get_evidence_provenance(db, project_id)
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
        metrics=get_biodiversity_metrics(db, project_id),
        provenance=provenance,
        sites=sites,
        recent_audio_files=recent_audio_files,
        recent_detections=recent_detections,
        job_counts_by_status={status: count for status, count in job_rows},
        top_species=[{"label": label, "count": count} for label, count in species_rows],
    )


@router.get("/projects/{project_id}/readiness")
def project_readiness(project_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return _project_readiness_data(project_id, db)


@router.get("/projects/{project_id}/evidence-package")
def project_evidence_package(project_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return _project_evidence_package(project_id, db)


@router.get("/sites", response_model=list[SiteRead])
def list_sites(project_id: str | None = None, db: Session = Depends(get_db)) -> list[Site]:
    query = select(Site)
    if project_id:
        query = query.where(Site.project_id == project_id)
    return list(db.scalars(query.order_by(Site.name)))


@router.post("/sites", response_model=SiteRead, status_code=201, dependencies=[Depends(require_admin_key)])
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


@router.post("/audio-files", response_model=AudioFileRead, status_code=201, dependencies=[Depends(require_admin_key)])
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


@router.post(
    "/audio-files/upload",
    response_model=AudioFileRead,
    status_code=201,
    dependencies=[Depends(require_admin_key)],
)
async def upload_audio_file(
    site_id: str = Form(...),
    duration_seconds: float | None = Form(default=None),
    recorded_at: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AudioFile:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found.")

    stored = await save_uploaded_wav(file, site_id)
    idempotency_key = f"sha256:{stored.sha256}"
    existing = db.scalar(
        select(AudioFile).where(AudioFile.site_id == site_id, AudioFile.idempotency_key == idempotency_key)
    )
    if existing is not None:
        ensure_processing_job(db, existing, job_type="birdnet_analysis")
        return existing

    from datetime import datetime

    parsed_recorded_at = datetime.fromisoformat(recorded_at) if recorded_at else None
    audio_file = AudioFile(
        site_id=site_id,
        file_name=stored.file_name,
        idempotency_key=idempotency_key,
        storage_uri=stored.storage_uri,
        content_type=stored.content_type,
        duration_seconds=duration_seconds,
        recorded_at=parsed_recorded_at,
        status="uploaded",
    )
    db.add(audio_file)
    db.flush()
    ensure_processing_job(db, audio_file, job_type="birdnet_analysis")
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


@router.post(
    "/processing-jobs",
    response_model=ProcessingJobRead,
    status_code=201,
    dependencies=[Depends(require_admin_key)],
)
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


def _run_processing_job(job_id: str, db: Session) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    if job.status == "completed":
        return job
    try:
        return run_job_once(db, job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/processing-jobs/{job_id}/run",
    response_model=ProcessingJobRead,
    dependencies=[Depends(require_admin_key)],
)
def run_processing_job(job_id: str, db: Session = Depends(get_db)) -> ProcessingJob:
    return _run_processing_job(job_id, db)


@router.post(
    "/processing-jobs/{job_id}/run-mock",
    response_model=ProcessingJobRead,
    dependencies=[Depends(require_admin_key)],
)
def run_processing_job_legacy(job_id: str, db: Session = Depends(get_db)) -> ProcessingJob:
    return _run_processing_job(job_id, db)


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


@router.patch(
    "/detections/{detection_id}",
    response_model=DetectionRead,
    dependencies=[Depends(require_admin_key)],
)
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
def list_raw_model_outputs(
    audio_file_id: str | None = None,
    project_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[RawModelOutput]:
    query = select(RawModelOutput)
    if project_id:
        query = query.join(AudioFile).join(Site).where(Site.project_id == project_id)
    if audio_file_id:
        query = query.where(RawModelOutput.audio_file_id == audio_file_id)
    return list(db.scalars(query.order_by(RawModelOutput.created_at.desc())))


@router.post("/reports", response_model=ReportRead, status_code=201, dependencies=[Depends(require_admin_key)])
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


def _csv_response(filename: str, rows: list[dict[str, object]], fieldnames: list[str]) -> Response:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _geojson_response(filename: str, features: list[dict[str, object]]) -> Response:
    return Response(
        content=json.dumps({"type": "FeatureCollection", "features": features}, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/detections.csv")
def export_detections_csv(project_id: str, db: Session = Depends(get_db)) -> Response:
    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    rows = db.execute(
        select(Project, Site, AudioFile, Detection)
        .join(Site, Site.project_id == Project.id)
        .join(AudioFile, AudioFile.site_id == Site.id)
        .join(Detection, Detection.audio_file_id == AudioFile.id)
        .where(Project.id == project_id)
        .order_by(Detection.created_at.desc())
    ).all()
    return _csv_response(
        "detections.csv",
        [
            {
                "project_id": project.id,
                "project_name": project.name,
                "site_id": site.id,
                "site_name": site.name,
                "audio_file_id": audio_file.id,
                "file_name": audio_file.file_name,
                "detection_id": detection.id,
                "label": detection.label,
                "detection_type": detection.detection_type,
                "confidence": detection.confidence,
                "start_seconds": detection.start_seconds,
                "end_seconds": detection.end_seconds,
                "review_status": detection.review_status,
                "evidence_level": provenance.evidence_level,
                "claim_status": provenance.claim_status,
                "created_at": detection.created_at.isoformat(),
            }
            for project, site, audio_file, detection in rows
        ],
        [
            "project_id",
            "project_name",
            "site_id",
            "site_name",
            "audio_file_id",
            "file_name",
            "detection_id",
            "label",
            "detection_type",
            "confidence",
            "start_seconds",
            "end_seconds",
            "review_status",
            "evidence_level",
            "claim_status",
            "created_at",
        ],
    )


@router.get("/exports/sites.csv")
def export_sites_csv(project_id: str, db: Session = Depends(get_db)) -> Response:
    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    sites = list(db.scalars(select(Site).where(Site.project_id == project_id).order_by(Site.name)))
    return _csv_response(
        "sites.csv",
        [
            {
                "site_id": site.id,
                "project_id": site.project_id,
                "name": site.name,
                "habitat_type": site.habitat_type or "",
                "latitude": site.latitude or "",
                "longitude": site.longitude or "",
                "evidence_level": provenance.evidence_level,
                "claim_status": provenance.claim_status,
                "created_at": site.created_at.isoformat(),
            }
            for site in sites
        ],
        ["site_id", "project_id", "name", "habitat_type", "latitude", "longitude", "evidence_level", "claim_status", "created_at"],
    )


@router.get("/exports/audio-files.csv")
def export_audio_files_csv(project_id: str, db: Session = Depends(get_db)) -> Response:
    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    audio_files = list(
        db.scalars(select(AudioFile).join(Site).where(Site.project_id == project_id).order_by(AudioFile.created_at.desc()))
    )
    return _csv_response(
        "audio-files.csv",
        [
            {
                "audio_file_id": audio_file.id,
                "site_id": audio_file.site_id,
                "file_name": audio_file.file_name,
                "storage_uri": audio_file.storage_uri,
                "duration_seconds": audio_file.duration_seconds or "",
                "status": audio_file.status,
                "evidence_level": provenance.evidence_level,
                "claim_status": provenance.claim_status,
                "created_at": audio_file.created_at.isoformat(),
            }
            for audio_file in audio_files
        ],
        ["audio_file_id", "site_id", "file_name", "storage_uri", "duration_seconds", "status", "evidence_level", "claim_status", "created_at"],
    )


@router.get("/exports/sites.geojson")
def export_sites_geojson(project_id: str, db: Session = Depends(get_db)) -> Response:
    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    sites = list(db.scalars(select(Site).where(Site.project_id == project_id).order_by(Site.name)))
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [site.longitude, site.latitude]},
            "properties": {
                "site_id": site.id,
                "project_id": site.project_id,
                "name": site.name,
                "habitat_type": site.habitat_type,
                "evidence_level": provenance.evidence_level,
                "claim_status": provenance.claim_status,
            },
        }
        for site in sites
        if site.latitude is not None and site.longitude is not None
    ]
    return _geojson_response("sites.geojson", features)


@router.get("/exports/detections.geojson")
def export_detections_geojson(project_id: str, db: Session = Depends(get_db)) -> Response:
    provenance = get_evidence_provenance(db, project_id)
    if provenance is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    rows = db.execute(
        select(Project, Site, AudioFile, Detection)
        .join(Site, Site.project_id == Project.id)
        .join(AudioFile, AudioFile.site_id == Site.id)
        .join(Detection, Detection.audio_file_id == AudioFile.id)
        .where(Project.id == project_id, Site.latitude.is_not(None), Site.longitude.is_not(None))
        .order_by(Detection.created_at.desc())
    ).all()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [site.longitude, site.latitude]},
            "properties": {
                "project_id": project.id,
                "project_name": project.name,
                "site_id": site.id,
                "site_name": site.name,
                "habitat_type": site.habitat_type,
                "audio_file_id": audio_file.id,
                "file_name": audio_file.file_name,
                "recorded_at": audio_file.recorded_at.isoformat() if audio_file.recorded_at else None,
                "detection_id": detection.id,
                "label": detection.label,
                "detection_type": detection.detection_type,
                "confidence": detection.confidence,
                "start_seconds": detection.start_seconds,
                "end_seconds": detection.end_seconds,
                "review_status": detection.review_status,
                "evidence_level": provenance.evidence_level,
                "claim_status": provenance.claim_status,
            },
        }
        for project, site, audio_file, detection in rows
    ]
    return _geojson_response("detections.geojson", features)


@router.get("/exports/evidence-package.md")
def export_evidence_package_markdown(project_id: str, db: Session = Depends(get_db)) -> Response:
    package = _project_evidence_package(project_id, db)
    return Response(
        content=_evidence_markdown(package),
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="evidence-package.md"'},
    )


@router.get("/exports/tnfd-biodiversity.json")
def export_tnfd_biodiversity_json(project_id: str, db: Session = Depends(get_db)) -> Response:
    package = _project_evidence_package(project_id, db)
    summary = package.get("summary") or {}
    metrics = package.get("metrics") or {}
    readiness = package.get("readiness") or {}

    tnfd_payload = {
        "framework": "TNFD v1.0 Nature-Related Financial Disclosures",
        "standard_reference": "LEAP (Locate, Evaluate, Assess, Prepare)",
        "disclosure_metric": "State of Nature - Acoustic Species Richness & Bioacoustic Integrity",
        "project": package.get("project"),
        "evidence_integrity": {
            "evidence_level": readiness.get("evidence_level"),
            "readiness_score": readiness.get("readiness_score"),
            "claim_status": readiness.get("claim_status"),
        },
        "indicators": {
            "monitored_sites_count": summary.get("site_count", 0),
            "recording_effort_hours": metrics.get("recording_hours", 0),
            "species_richness_observed": metrics.get("species_richness", 0),
            "shannon_diversity_index": metrics.get("species_diversity_shannon", 0.0),
            "detections_per_effort_hour": metrics.get("detections_per_hour", 0.0),
            "expert_confirmed_percent": metrics.get("confirmed_detection_percent", 0.0),
        },
        "sites": package.get("sites", []),
        "top_species_observed": package.get("top_species", []),
        "governance_note": package.get("disclaimer"),
    }
    return Response(
        content=json.dumps(tnfd_payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="tnfd-biodiversity-disclosure.json"'},
    )


@router.get("/exports/esrs-compliance.json")
def export_esrs_compliance_json(project_id: str, db: Session = Depends(get_db)) -> Response:
    package = _project_evidence_package(project_id, db)
    esrs_payload = {
        "standard": "CSRD - ESRS E4 Biodiversity and Ecosystems",
        "disclosure_topic": "E4-4 Impact metrics on biodiversity and ecosystems change",
        "evidence_package": package,
    }
    return Response(
        content=json.dumps(esrs_payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="esrs-e4-compliance.json"'},
    )

