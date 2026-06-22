from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from backend.app.models import AudioFile, Detection, Project, RawModelOutput, Site
from backend.app.schemas.api import BiodiversityMetrics, EvidenceProvenance, ProjectSummary
from backend.app.services.birdnet_processing import shannon_diversity


def get_project_summary(db: Session, project_id: str) -> ProjectSummary | None:
    project = db.get(Project, project_id)
    if project is None:
        return None

    site_count = db.scalar(select(func.count(Site.id)).where(Site.project_id == project_id)) or 0
    audio_file_count = (
        db.scalar(select(func.count(AudioFile.id)).join(Site).where(Site.project_id == project_id)) or 0
    )
    detection_count = (
        db.scalar(select(func.count(Detection.id)).join(AudioFile).join(Site).where(Site.project_id == project_id))
        or 0
    )
    species_richness = (
        db.scalar(
            select(func.count(distinct(Detection.species_reference_id)))
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id, Detection.detection_type == "species")
        )
        or 0
    )
    noise_detections = (
        db.scalar(
            select(func.count(Detection.id))
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id, Detection.detection_type == "sound_class")
        )
        or 0
    )

    return ProjectSummary(
        project_id=project.id,
        project_name=project.name,
        site_count=site_count,
        audio_file_count=audio_file_count,
        detection_count=detection_count,
        species_richness=species_richness,
        biodiversity_activity_score=round(min(100.0, species_richness * 20 + detection_count * 2), 2),
        noise_score=round(min(100.0, noise_detections * 15), 2),
    )


def get_biodiversity_metrics(db: Session, project_id: str) -> BiodiversityMetrics | None:
    project = db.get(Project, project_id)
    if project is None:
        return None

    duration_seconds = (
        db.scalar(
            select(func.coalesce(func.sum(AudioFile.duration_seconds), 0.0))
            .join(Site)
            .where(Site.project_id == project_id)
        )
        or 0.0
    )
    recording_hours = round(float(duration_seconds) / 3600, 4)
    species_labels = list(
        db.scalars(
            select(Detection.label)
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id, Detection.detection_type == "species")
        )
    )
    detection_count = len(species_labels)
    confirmed_count = (
        db.scalar(
            select(func.count(Detection.id))
            .join(AudioFile)
            .join(Site)
            .where(
                Site.project_id == project_id,
                Detection.detection_type == "species",
                Detection.review_status == "confirmed",
            )
        )
        or 0
    )
    species_richness = len(set(species_labels))
    return BiodiversityMetrics(
        project_id=project_id,
        recording_hours=recording_hours,
        species_richness=species_richness,
        detections_per_hour=round(detection_count / recording_hours, 2) if recording_hours else float(detection_count),
        confirmed_detection_percent=round((confirmed_count / detection_count) * 100, 2) if detection_count else 0.0,
        species_diversity_shannon=shannon_diversity(species_labels),
    )


def get_evidence_provenance(db: Session, project_id: str) -> EvidenceProvenance | None:
    project = db.get(Project, project_id)
    if project is None:
        return None

    audio_rows = list(db.scalars(select(AudioFile).join(Site).where(Site.project_id == project_id)))
    raw_rows = list(db.scalars(select(RawModelOutput).join(AudioFile).join(Site).where(Site.project_id == project_id)))
    modes = [str(row.payload.get("mode", "unknown")) for row in raw_rows]
    real_outputs = sum(1 for mode in modes if mode == "configured")
    no_detection_outputs = sum(1 for mode in modes if mode == "configured_no_detections")
    simulated_outputs = sum(
        1
        for row, mode in zip(raw_rows, modes, strict=True)
        if "simulated" in mode
        or str(row.payload.get("contract", "")).startswith("mock_")
        or str(row.output_format).startswith("mock_")
    )
    simulation_only = bool(raw_rows) and real_outputs == 0 and simulated_outputs > 0
    local_audio = sum(1 for audio in audio_rows if audio.storage_uri.startswith("file://"))
    simulated_audio = sum(1 for audio in audio_rows if audio.storage_uri.startswith("simulation://"))
    external_audio = len(audio_rows) - local_audio - simulated_audio
    confirmed_detections = (
        db.scalar(
            select(func.count(Detection.id))
            .join(AudioFile)
            .join(Site)
            .where(Site.project_id == project_id, Detection.review_status == "confirmed")
        )
        or 0
    )
    has_reviewed_real_evidence = bool(real_outputs and confirmed_detections >= 20)

    if simulation_only:
        evidence_level = "simulation"
        claim_status = "Demo rehearsal only"
        disclaimer = "Do not present these values as ecological findings; this project currently uses simulated model outputs."
        next_required_proof = "Upload approved field WAV recordings and run configured BirdNET inference."
    elif has_reviewed_real_evidence:
        evidence_level = "real_inference"
        claim_status = "Reviewed real evidence"
        disclaimer = "Real model outputs and confirmed reviews are present; keep claims conservative and method-bound."
        next_required_proof = "Expand field coverage and document reviewer methodology."
    elif real_outputs:
        evidence_level = "real_inference"
        claim_status = "Real inference, review required"
        disclaimer = "Real model outputs are present, but detections still need human validation before ecological claims."
        next_required_proof = "Confirm at least 20 representative detections with a trained reviewer."
    else:
        evidence_level = "workflow"
        claim_status = "Workflow verified"
        disclaimer = "The software flow is working, but ecological evidence has not been generated yet."
        next_required_proof = "Configure BirdNET and process real WAV recordings."

    return EvidenceProvenance(
        project_id=project_id,
        evidence_level=evidence_level,
        simulation_only=simulation_only,
        can_make_ecological_claims=has_reviewed_real_evidence,
        real_birdnet_outputs=real_outputs,
        simulated_outputs=simulated_outputs,
        configured_no_detection_outputs=no_detection_outputs,
        local_audio_files=local_audio,
        simulated_audio_files=simulated_audio,
        external_audio_records=external_audio,
        confirmed_detections=confirmed_detections,
        claim_status=claim_status,
        disclaimer=disclaimer,
        next_required_proof=next_required_proof,
    )
