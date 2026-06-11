from sqlalchemy import select

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models import AudioFile, Detection, Organization, ProcessingJob, Project, RawModelOutput, Site
from backend.app.services.job_state import transition_job


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_metadata_imports():
    from backend.app.models import Base

    assert "organizations" in Base.metadata.tables
    assert "processing_jobs" in Base.metadata.tables
    assert "impact_snapshots" in Base.metadata.tables


def test_seed_script_is_idempotent(db_session):
    from database.seed.seed_data import seed

    first = seed(db_session)
    second = seed(db_session)

    assert first["organization_id"] == second["organization_id"]
    assert len(db_session.scalars(select(Organization)).all()) == 1


def test_create_audio_file_creates_processing_job(client, db_session):
    site = db_session.scalar(select(Site))

    response = client.post(
        "/audio-files",
        json={
            "site_id": site.id,
            "file_name": "sample.wav",
            "storage_uri": "s3://example/sample.wav",
            "content_type": "audio/wav",
            "duration_seconds": 31.5,
        },
    )

    assert response.status_code == 201
    audio_file_id = response.json()["id"]
    job = db_session.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))
    assert job is not None
    assert job.status == "queued"


def test_audio_file_idempotency_key_prevents_duplicate_jobs(client, db_session):
    site = db_session.scalar(select(Site))
    payload = {
        "site_id": site.id,
        "file_name": "retry.wav",
        "storage_uri": "s3://example/retry.wav",
        "idempotency_key": "upload-123",
    }

    first = client.post("/audio-files", json=payload)
    second = client.post("/audio-files", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    jobs = db_session.scalars(select(ProcessingJob).where(ProcessingJob.audio_file_id == first.json()["id"])).all()
    assert len(jobs) == 1


def test_mock_processing_stores_normalized_detections(client, db_session):
    site = db_session.scalar(select(Site))
    audio_response = client.post(
        "/audio-files",
        json={
            "site_id": site.id,
            "file_name": "mock.wav",
            "storage_uri": "s3://example/mock.wav",
        },
    )
    audio_file_id = audio_response.json()["id"]
    job = db_session.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))

    response = client.post(f"/processing-jobs/{job.id}/run-mock")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    detections = db_session.scalars(select(Detection).where(Detection.audio_file_id == audio_file_id)).all()
    raw_outputs = db_session.scalars(select(RawModelOutput).where(RawModelOutput.audio_file_id == audio_file_id)).all()
    assert {d.detection_type for d in detections} == {"species", "sound_class"}
    assert all(d.confidence > 0 for d in detections)
    assert len(raw_outputs) == 1
    assert raw_outputs[0].payload["contract"] == "mock_audio_analysis.v1"

    raw_response = client.get("/raw-model-outputs")
    assert raw_response.status_code == 200
    assert raw_response.json()[0]["payload"]["contract"] == "mock_audio_analysis.v1"


def test_job_state_rejects_completed_to_queued(db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="state.wav", storage_uri="s3://example/state.wav")
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, status="completed")
    db_session.add(job)
    db_session.flush()

    with pytest.raises(ValueError):
        transition_job(db_session, job, "queued")


def test_run_mock_rejects_unsupported_job_type(client, db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="unsupported.wav", storage_uri="s3://example/unsupported.wav")
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, job_type="birdnet_analysis")
    db_session.add(job)
    db_session.commit()

    response = client.post(f"/processing-jobs/{job.id}/run-mock")

    assert response.status_code == 400
    assert "Unsupported processing job type" in response.json()["detail"]


def test_database_constraints_reject_invalid_processing_job_status(db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="bad-status.wav", storage_uri="s3://example/bad-status.wav")
    db_session.add(audio_file)
    db_session.flush()
    db_session.add(ProcessingJob(audio_file_id=audio_file.id, status="pending"))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_summary_returns_seeded_shape(client, db_session):
    project = db_session.scalar(select(Project))
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="summary.wav", storage_uri="s3://example/summary.wav")
    db_session.add(audio_file)
    db_session.commit()
    job = ProcessingJob(audio_file_id=audio_file.id)
    db_session.add(job)
    db_session.commit()
    client.post(f"/processing-jobs/{job.id}/run-mock")

    response = client.get(f"/projects/{project.id}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project.id
    assert body["site_count"] == 1
    assert body["audio_file_count"] >= 1
    assert body["detection_count"] >= 2
    assert body["metric_label"] == "prototype_indicator"


def test_report_shell_endpoints(client, db_session):
    project = db_session.scalar(select(Project))

    create_response = client.post(
        "/reports",
        json={
            "project_id": project.id,
            "title": "Prototype Biodiversity Summary",
            "report_type": "prototype_summary",
        },
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == "draft"

    list_response = client.get("/reports")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Prototype Biodiversity Summary"
