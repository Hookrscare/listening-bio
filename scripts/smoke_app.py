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

        job = db.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_response.json()["id"]))
        run_response = client.post(f"/processing-jobs/{job.id}/run-mock")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "completed"
        checks.append("mock processing completes")

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
        assert dashboard["recent_detections"]
        checks.append("dashboard aggregate")

        assert "BioSignal Command" in client.get("/app/").text
        checks.append("frontend served")

        print("Smoke verification passed:")
        for check in checks:
            print(f"- {check}")
        return 0
    finally:
        app.dependency_overrides.clear()
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
