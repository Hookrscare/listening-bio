from sqlalchemy import func, select

from backend.app.api.deps import hash_api_key
from backend.app.models import APIKey, AudioFile, Detection, Organization, Project, ReviewEvent, Site, UsageEvent


def _authorize(db_session, organization_id: str, raw_key: str = "lb_test_partner_key") -> dict[str, str]:
    db_session.add(
        APIKey(
            organization_id=organization_id,
            key_hash=hash_api_key(raw_key),
            name="test integration",
            prefix=raw_key[:8],
        )
    )
    db_session.commit()
    return {"X-API-Key": raw_key}


def _seed_audio(db_session) -> tuple[Organization, AudioFile]:
    organization = db_session.scalar(select(Organization).order_by(Organization.created_at))
    site = db_session.scalar(
        select(Site).join(Project, Project.id == Site.project_id).where(Project.organization_id == organization.id)
    )
    audio_file = AudioFile(
        site_id=site.id,
        file_name="partner-recording.wav",
        storage_uri="s3://partner/partner-recording.wav",
        content_type="audio/wav",
        duration_seconds=12,
        status="uploaded",
    )
    db_session.add(audio_file)
    db_session.commit()
    return organization, audio_file


def test_evidence_api_requires_api_key(client, db_session):
    _, audio_file = _seed_audio(db_session)
    response = client.post(
        "/v1/evidence/model-runs",
        json={
            "audio_file_id": audio_file.id,
            "model_name": "Partner Model",
            "model_version": "1",
            "detections": [],
        },
    )
    assert response.status_code == 401


def test_external_model_run_stores_normalized_evidence_and_usage(client, db_session):
    organization, audio_file = _seed_audio(db_session)
    headers = _authorize(db_session, organization.id)

    response = client.post(
        "/v1/evidence/model-runs",
        headers=headers,
        json={
            "audio_file_id": audio_file.id,
            "model_name": "Partner Classifier",
            "model_version": "2026.08",
            "provider": "University Lab",
            "detections": [
                {
                    "common_name": "American Robin",
                    "scientific_name": "Turdus migratorius",
                    "confidence": 0.91,
                    "start_seconds": 1.5,
                    "end_seconds": 4.0,
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["imported_detections"] == 1
    detection = db_session.get(Detection, payload["detection_ids"][0])
    assert detection.label == "American Robin"
    assert detection.review_status == "unreviewed"
    assert db_session.scalar(select(func.count(UsageEvent.id))) == 1


def test_api_key_cannot_import_into_another_organization(client, db_session):
    organization, _ = _seed_audio(db_session)
    headers = _authorize(db_session, organization.id)
    other_organization = Organization(name="Other Lab")
    db_session.add(other_organization)
    db_session.flush()
    other_project = Project(organization_id=other_organization.id, name="Private Survey")
    db_session.add(other_project)
    db_session.flush()
    other_site = Site(project_id=other_project.id, name="Private Site")
    db_session.add(other_site)
    db_session.flush()
    other_audio = AudioFile(
        site_id=other_site.id,
        file_name="private.wav",
        storage_uri="s3://private/private.wav",
        content_type="audio/wav",
        status="uploaded",
    )
    db_session.add(other_audio)
    db_session.commit()

    response = client.post(
        "/v1/evidence/model-runs",
        headers=headers,
        json={
            "audio_file_id": other_audio.id,
            "model_name": "Partner Classifier",
            "model_version": "1",
            "detections": [],
        },
    )
    assert response.status_code == 404


def test_review_creates_immutable_event_and_updates_cached_status(client, db_session):
    organization, audio_file = _seed_audio(db_session)
    headers = _authorize(db_session, organization.id)
    imported = client.post(
        "/v1/evidence/model-runs",
        headers=headers,
        json={
            "audio_file_id": audio_file.id,
            "model_name": "Partner Classifier",
            "model_version": "1",
            "detections": [
                {
                    "common_name": "Northern Cardinal",
                    "confidence": 0.88,
                    "start_seconds": 0,
                    "end_seconds": 3,
                }
            ],
        },
    ).json()
    detection_id = imported["detection_ids"][0]

    response = client.post(
        f"/v1/evidence/detections/{detection_id}/reviews",
        headers=headers,
        json={"new_status": "confirmed", "notes": "Verified against the source clip."},
    )

    assert response.status_code == 201
    assert response.json()["previous_status"] == "unreviewed"
    assert db_session.get(Detection, detection_id).review_status == "confirmed"
    event = db_session.scalar(select(ReviewEvent).where(ReviewEvent.detection_id == detection_id))
    assert event.previous_status == "unreviewed"
    assert event.new_status == "confirmed"

    history = client.get(f"/v1/evidence/detections/{detection_id}/reviews", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1
