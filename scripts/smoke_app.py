import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import Base, Detection, ProcessingJob
from database.seed.seed_data import seed
from fastapi.testclient import TestClient


def tiny_wav_bytes() -> bytes:
    return (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00"
        b"data\x00\x00\x00\x00"
    )


def main() -> int:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = session_factory()
    seed(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        checks: list[str] = []

        assert client.get("/health").json()["status"] == "ok"
        checks.append("health endpoint")

        org_id = client.get("/organizations").json()[0]["id"]
        project_response = client.post(
            "/projects",
            json={
                "organization_id": org_id,
                "name": "Smoke Wetland Pilot",
                "description": "Smoke-created project.",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]
        checks.append("project creation")

        site_response = client.post(
            "/sites",
            json={
                "project_id": project_id,
                "name": "Smoke Meadow",
                "habitat_type": "restored meadow",
                "latitude": 40.72,
                "longitude": -74.01,
            },
        )
        assert site_response.status_code == 201
        checks.append("site creation")

        audio_response = client.post(
            "/audio-files",
            json={
                "site_id": site_response.json()["id"],
                "file_name": "smoke-survey.wav",
                "storage_uri": "s3://prototype-audio/smoke-survey.wav",
                "duration_seconds": 12.4,
                "idempotency_key": "smoke-survey",
            },
        )
        assert audio_response.status_code == 201
        checks.append("audio metadata creates queued job")

        upload_response = client.post(
            "/audio-files/upload",
            data={"site_id": site_response.json()["id"], "duration_seconds": "18.0"},
            files={"file": ("smoke-upload.wav", tiny_wav_bytes(), "audio/wav")},
        )
        assert upload_response.status_code == 201
        checks.append("WAV upload creates BirdNET job")

        job = db.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_response.json()["id"]))
        run_response = client.post(f"/processing-jobs/{job.id}/run-mock")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "completed"
        checks.append("mock processing completes")

        birdnet_job = db.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == upload_response.json()["id"]))
        birdnet_response = client.post(f"/processing-jobs/{birdnet_job.id}/run-mock")
        assert birdnet_response.status_code == 200
        assert birdnet_response.json()["status"] == "completed"
        checks.append("BirdNET adapter processing completes")

        detections = client.get(f"/detections?project_id={project_id}").json()
        assert len(detections) >= 2
        checks.append("detections are stored")

        detection = db.scalar(select(Detection).where(Detection.audio_file_id == audio_response.json()["id"]))
        review_response = client.patch(f"/detections/{detection.id}", json={"review_status": "confirmed"})
        assert review_response.json()["review_status"] == "confirmed"
        checks.append("detection review mutation")

        report_response = client.post(
            "/reports",
            json={"project_id": project_id, "title": "Smoke Prototype Report", "report_type": "prototype_summary"},
        )
        assert report_response.status_code == 201
        checks.append("report shell creation")

        dashboard = client.get(f"/projects/{project_id}/dashboard").json()
        assert dashboard["summary"]["detection_count"] >= 2
        assert dashboard["metrics"]["species_richness"] >= 1
        assert dashboard["recent_detections"]
        checks.append("dashboard aggregate")

        csv_response = client.get(f"/exports/detections.csv?project_id={project_id}")
        assert csv_response.status_code == 200
        assert "American Robin" in csv_response.text
        checks.append("CSV export")

        frontend_html = client.get("/app/").text
        assert "BioSignal Command" in frontend_html
        assert "Habitat monitoring map" in frontend_html
        checks.append("frontend and map shell served")

        print("Smoke verification passed:")
        for check in checks:
            print(f"- {check}")
        return 0
    finally:
        app.dependency_overrides.clear()
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
