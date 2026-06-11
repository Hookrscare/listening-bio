from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from backend.app.models import AudioFile, Detection, Project, Site
from backend.app.schemas.api import BiodiversityMetrics, ProjectSummary
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
