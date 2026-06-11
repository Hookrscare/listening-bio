from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import AIModel, AudioFile, Detection, ProcessingJob, RawModelOutput, SoundClass, SpeciesReference
from backend.app.services.job_state import sync_audio_status, transition_job


def ensure_processing_job(db: Session, audio_file: AudioFile, job_type: str = "mock_audio_analysis") -> ProcessingJob:
    existing = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.audio_file_id == audio_file.id,
            ProcessingJob.job_type == job_type,
            ProcessingJob.status.in_(["queued", "running", "completed"]),
        )
    )
    if existing is not None:
        return existing

    job = ProcessingJob(audio_file_id=audio_file.id, status="queued", job_type=job_type)
    db.add(job)
    sync_audio_status(audio_file, job.status)
    db.commit()
    db.refresh(job)
    return job


def run_mock_processing(db: Session, job: ProcessingJob) -> ProcessingJob:
    if job.status in {"completed", "cancelled"}:
        return job

    audio_file = db.get(AudioFile, job.audio_file_id)
    if audio_file is None:
        transition_job(db, job, "failed", "Audio file not found.")
        db.commit()
        db.refresh(job)
        return job

    if job.status == "failed":
        transition_job(db, job, "queued")
    transition_job(db, job, "running")
    sync_audio_status(audio_file, job.status)
    db.flush()

    bird_model = db.scalar(select(AIModel).where(AIModel.name == "BirdNET Analyzer"))
    yamnet_model = db.scalar(select(AIModel).where(AIModel.name == "YAMNet"))
    species = db.scalar(select(SpeciesReference).where(SpeciesReference.scientific_name == "Turdus migratorius"))
    sound_class = db.scalar(select(SoundClass).where(SoundClass.label == "Rain"))

    raw_payload = {
        "contract": "mock_audio_analysis.v1",
        "outputs": [
            {"model": "BirdNET Analyzer", "label": "American Robin", "confidence": 0.87, "start": 4.2, "end": 7.9},
            {"model": "YAMNet", "label": "Rain", "confidence": 0.74, "start": 12.0, "end": 18.5},
        ],
    }
    db.add(
        RawModelOutput(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=bird_model.id if bird_model else None,
            output_format="mock_json",
            payload=raw_payload,
        )
    )

    detections = [
        Detection(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=bird_model.id if bird_model else None,
            species_reference_id=species.id if species else None,
            detection_type="species",
            label=species.common_name if species and species.common_name else "American Robin",
            confidence=0.87,
            start_seconds=4.2,
            end_seconds=7.9,
        ),
        Detection(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=yamnet_model.id if yamnet_model else None,
            sound_class_id=sound_class.id if sound_class else None,
            detection_type="sound_class",
            label=sound_class.label if sound_class else "Rain",
            confidence=0.74,
            start_seconds=12.0,
            end_seconds=18.5,
        ),
    ]
    db.add_all(detections)

    transition_job(db, job, "completed")
    sync_audio_status(audio_file, job.status)
    db.commit()
    db.refresh(job)
    return job
