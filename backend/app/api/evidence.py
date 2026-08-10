from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_organization
from backend.app.db.session import get_db
from backend.app.models import (
    AIModel,
    AudioFile,
    Detection,
    Membership,
    Organization,
    ProcessingJob,
    RawModelOutput,
    ReviewEvent,
    Site,
    SpeciesReference,
    UsageEvent,
)


router = APIRouter(prefix="/v1/evidence", tags=["Evidence API"])


class DetectionImport(BaseModel):
    common_name: str = Field(min_length=1, max_length=255)
    scientific_name: str | None = Field(default=None, max_length=255)
    confidence: float = Field(ge=0, le=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_interval(self) -> "DetectionImport":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        return self


class ModelRunImport(BaseModel):
    audio_file_id: str
    model_name: str = Field(min_length=1, max_length=120)
    model_version: str = Field(min_length=1, max_length=80)
    provider: str | None = Field(default=None, max_length=120)
    detections: list[DetectionImport] = Field(max_length=10_000)
    raw_output: dict[str, object] | None = None


class DetectionReviewCreate(BaseModel):
    new_status: Literal["unreviewed", "confirmed", "rejected"]
    reviewer_id: str | None = None
    notes: str | None = Field(default=None, max_length=4000)


def _owned_audio_file(db: Session, audio_file_id: str, organization_id: str) -> AudioFile | None:
    return db.scalar(
        select(AudioFile)
        .join(Site, Site.id == AudioFile.site_id)
        .where(AudioFile.id == audio_file_id, Site.project.has(organization_id=organization_id))
    )


def _owned_detection(
    db: Session,
    detection_id: str,
    organization_id: str,
    *,
    for_update: bool = False,
) -> Detection | None:
    query = (
        select(Detection)
        .join(AudioFile, AudioFile.id == Detection.audio_file_id)
        .join(Site, Site.id == AudioFile.site_id)
        .where(Detection.id == detection_id, Site.project.has(organization_id=organization_id))
    )
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


@router.post("/model-runs", status_code=status.HTTP_201_CREATED)
def import_model_run(
    payload: ModelRunImport,
    db: Session = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
) -> dict[str, object]:
    audio_file = _owned_audio_file(db, payload.audio_file_id, organization.id)
    if audio_file is None:
        raise HTTPException(status_code=404, detail="Audio file not found.")

    model = db.scalar(select(AIModel).where(AIModel.name == payload.model_name, AIModel.version == payload.model_version))
    if model is None:
        model = AIModel(
            name=payload.model_name,
            version=payload.model_version,
            model_type="external_bioacoustic_classifier",
            provider=payload.provider,
        )
        db.add(model)
        db.flush()

    job = ProcessingJob(audio_file_id=audio_file.id, status="completed", job_type="external_model_import")
    db.add(job)
    db.flush()

    raw_payload = payload.raw_output or {"detections": [item.model_dump() for item in payload.detections]}
    db.add(
        RawModelOutput(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=model.id,
            output_format="external_json",
            payload={
                "model_name": payload.model_name,
                "model_version": payload.model_version,
                "provider": payload.provider,
                "output": raw_payload,
            },
        )
    )

    detection_ids: list[str] = []
    for imported in payload.detections:
        species = None
        if imported.scientific_name:
            species = db.scalar(select(SpeciesReference).where(SpeciesReference.scientific_name == imported.scientific_name))
            if species is None:
                species = SpeciesReference(scientific_name=imported.scientific_name, common_name=imported.common_name)
                db.add(species)
                db.flush()
        detection = Detection(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=model.id,
            species_reference_id=species.id if species else None,
            detection_type="species",
            label=imported.common_name,
            confidence=imported.confidence,
            start_seconds=imported.start_seconds,
            end_seconds=imported.end_seconds,
            review_status="unreviewed",
        )
        db.add(detection)
        db.flush()
        detection_ids.append(detection.id)

    db.add(
        UsageEvent(
            organization_id=organization.id,
            event_type="evidence_import_count",
            quantity=float(len(detection_ids)),
            resource_id=audio_file.id,
        )
    )
    audio_file.status = "processed"
    db.commit()
    return {
        "model_run_id": job.id,
        "audio_file_id": audio_file.id,
        "imported_detections": len(detection_ids),
        "detection_ids": detection_ids,
    }


@router.post("/detections/{detection_id}/reviews", status_code=status.HTTP_201_CREATED)
def append_detection_review(
    detection_id: str,
    payload: DetectionReviewCreate,
    db: Session = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
) -> dict[str, str]:
    detection = _owned_detection(db, detection_id, organization.id, for_update=True)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found.")
    if payload.reviewer_id is not None:
        membership = db.scalar(
            select(Membership).where(
                Membership.organization_id == organization.id,
                Membership.user_id == payload.reviewer_id,
            )
        )
        if membership is None:
            raise HTTPException(status_code=400, detail="Reviewer is not a member of this organization.")

    previous_status = detection.review_status
    event = ReviewEvent(
        detection_id=detection.id,
        reviewer_id=payload.reviewer_id,
        previous_status=previous_status,
        new_status=payload.new_status,
        notes=payload.notes,
    )
    db.add(event)
    detection.review_status = payload.new_status
    db.commit()
    return {
        "review_event_id": event.id,
        "detection_id": detection.id,
        "previous_status": previous_status,
        "current_status": detection.review_status,
    }


@router.get("/detections/{detection_id}/reviews")
def list_detection_reviews(
    detection_id: str,
    db: Session = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
) -> list[dict[str, object]]:
    detection = _owned_detection(db, detection_id, organization.id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found.")
    events = list(
        db.scalars(select(ReviewEvent).where(ReviewEvent.detection_id == detection.id).order_by(ReviewEvent.created_at))
    )
    db.commit()
    return [
        {
            "id": event.id,
            "detection_id": event.detection_id,
            "reviewer_id": event.reviewer_id,
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "notes": event.notes,
            "created_at": event.created_at,
        }
        for event in events
    ]
