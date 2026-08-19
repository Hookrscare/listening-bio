import sys
import json

from sqlalchemy import select

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models import AudioFile, Detection, Organization, ProcessingJob, Project, RawModelOutput, Site
from backend.app.config import Settings, get_settings
from backend.app.main import app
from backend.app.services.job_state import transition_job


def tiny_wav_bytes() -> bytes:
    return (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00"
        b"data\x00\x00\x00\x00"
    )


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_key_protects_write_routes_when_configured(client, db_session):
    app.dependency_overrides[get_settings] = lambda: Settings(admin_api_key="test-admin-key")
    organization = db_session.scalar(select(Organization))
    payload = {"organization_id": organization.id, "name": "Protected Pilot"}

    assert client.get("/projects").status_code == 200
    assert client.post("/projects", json=payload).status_code == 401
    assert client.post("/projects", json=payload, headers={"X-Admin-Key": "wrong"}).status_code == 403

    response = client.post("/projects", json=payload, headers={"X-Admin-Key": "test-admin-key"})
    assert response.status_code == 201


def test_birdnet_status_endpoint(client):
    response = client.get("/integrations/birdnet/status")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] in {"simulated", "configured"}
    assert "csv" in body["supported_outputs"]
    assert "{input}" in body["recommended_command"]


def test_cors_allows_local_frontend(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_frontend_is_served_by_backend(client):
    response = client.get("/app/")

    assert response.status_code == 200
    assert "Listening.bio | Biodiversity, heard" in response.text
    assert 'id="evidenceGate"' in response.text
    assert 'id="claimEligibility"' in response.text
    assert 'id="biosphereCanvas"' in response.text
    assert 'type="module" src="./scene.js?v=listening-bio-final"' in response.text
    assert "Demonstration data, not field evidence" in client.get("/app/app.js").text
    assert "THREE.ShaderMaterial" in client.get("/app/scene.js").text


def test_favicon_does_not_404(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 204


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


def test_wav_upload_creates_birdnet_processing_job(client, db_session):
    site = db_session.scalar(select(Site))

    response = client.post(
        "/audio-files/upload",
        data={"site_id": site.id, "duration_seconds": "6.5"},
        files={"file": ("field-recording.wav", tiny_wav_bytes(), "audio/wav")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_name"] == "field-recording.wav"
    assert body["storage_uri"].startswith("file://")
    job = db_session.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == body["id"]))
    assert job is not None
    assert job.job_type == "birdnet_analysis"


def test_processing_job_run_endpoint_executes_analysis(client, db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="runner.wav", storage_uri="s3://example/runner.wav")
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, status="queued", job_type="mock_audio_analysis")
    db_session.add(job)
    db_session.commit()

    response = client.post(f"/processing-jobs/{job.id}/run")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_central_park_pilot_simulation_is_repeatable(db_session):
    from scripts.simulate_central_park_pilot import PROJECT_EXTERNAL_ID, SIMULATION_TAG, simulate

    first = simulate(db_session, recordings_per_site=2, seed_value=7)
    second = simulate(db_session, recordings_per_site=2, seed_value=7)
    project = db_session.scalar(select(Project).where(Project.external_id == PROJECT_EXTERNAL_ID))
    raw_output = db_session.scalar(
        select(RawModelOutput)
        .join(AudioFile, RawModelOutput.audio_file_id == AudioFile.id)
        .join(Site, AudioFile.site_id == Site.id)
        .where(Site.project_id == project.id)
    )

    assert first["sites"] == 5
    assert first["audio_files"] == 10
    assert second["audio_files"] == 10
    assert raw_output.payload["mode"] == "simulated_pilot"
    assert raw_output.payload["simulation_tag"] == SIMULATION_TAG


def test_wav_upload_rejects_non_wav(client, db_session):
    site = db_session.scalar(select(Site))

    response = client.post(
        "/audio-files/upload",
        data={"site_id": site.id},
        files={"file": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400


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


def test_run_job_rejects_unsupported_job_type(client, db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="unsupported.wav", storage_uri="s3://example/unsupported.wav")
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, job_type="unknown_analysis")
    db_session.add(job)
    db_session.commit()

    response = client.post(f"/processing-jobs/{job.id}/run-mock")

    assert response.status_code == 400
    assert "Unsupported processing job type" in response.json()["detail"]


def test_birdnet_processing_stores_normalized_species(client, db_session):
    site = db_session.scalar(select(Site))
    upload_response = client.post(
        "/audio-files/upload",
        data={"site_id": site.id, "duration_seconds": "30"},
        files={"file": ("birdnet.wav", tiny_wav_bytes(), "audio/wav")},
    )
    audio_file_id = upload_response.json()["id"]
    job = db_session.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))

    response = client.post(f"/processing-jobs/{job.id}/run-mock")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    detections = db_session.scalars(select(Detection).where(Detection.audio_file_id == audio_file_id)).all()
    raw_output = db_session.scalar(select(RawModelOutput).where(RawModelOutput.audio_file_id == audio_file_id))
    assert raw_output.payload["contract"] == "birdnet_analysis.v1"
    assert raw_output.output_format == "birdnet_json"
    if raw_output.payload.get("mode") == "simulated":
        assert {d.label for d in detections} >= {"American Robin", "Northern Cardinal"}
    else:
        assert raw_output.payload.get("mode") in {"configured", "configured_no_detections"}


def test_birdnet_csv_table_parser_normalizes_real_outputs(db_session, tmp_path):
    from backend.app.services.birdnet_processing import parse_birdnet_output_file

    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="birdnet-table.wav", storage_uri="file:///tmp/birdnet-table.wav")
    csv_path = tmp_path / "birdnet-results.csv"
    csv_path.write_text(
        "Begin Time (s),End Time (s),Scientific name,Common name,Confidence\n"
        "0.0,3.0,Poecile atricapillus,Black-capped Chickadee,0.7889\n"
    )

    results = parse_birdnet_output_file(csv_path, audio_file)

    assert results == [
        {
            "label": "Poecile atricapillus_Black-capped Chickadee",
            "confidence": 0.7889,
            "start_seconds": 0.0,
            "end_seconds": 3.0,
        }
    ]


def test_configured_birdnet_no_detections_does_not_fallback(monkeypatch, db_session, tmp_path):
    from backend.app.config import get_settings
    from backend.app.workers.processing_worker import run_job_once

    runner = tmp_path / "empty_birdnet.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "output_dir = Path(sys.argv[2])\n"
        "output_dir.mkdir(parents=True, exist_ok=True)\n"
        "(output_dir / 'empty.csv').write_text('Begin Time (s),End Time (s),Scientific name,Common name,Confidence\\n')\n"
    )
    audio_path = tmp_path / "field.wav"
    audio_path.write_bytes(tiny_wav_bytes())
    monkeypatch.setenv("BIRDNET_COMMAND", f'"{sys.executable}" "{runner}" {{input}} {{output_dir}}')
    get_settings.cache_clear()

    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="field.wav", storage_uri=audio_path.as_uri())
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, status="queued", job_type="birdnet_analysis")
    db_session.add(job)
    db_session.commit()

    completed = run_job_once(db_session, job)

    raw_output = db_session.scalar(select(RawModelOutput).where(RawModelOutput.audio_file_id == audio_file.id))
    detections = db_session.scalars(select(Detection).where(Detection.audio_file_id == audio_file.id)).all()
    assert completed.status == "completed"
    assert raw_output.payload["mode"] == "configured_no_detections"
    assert detections == []
    monkeypatch.delenv("BIRDNET_COMMAND", raising=False)
    get_settings.cache_clear()


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


def test_project_dashboard_contract(client, db_session):
    project = db_session.scalar(select(Project))
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="dashboard.wav", storage_uri="s3://example/dashboard.wav")
    db_session.add(audio_file)
    db_session.commit()
    job = ProcessingJob(audio_file_id=audio_file.id)
    db_session.add(job)
    db_session.commit()
    client.post(f"/processing-jobs/{job.id}/run-mock")

    response = client.get(f"/projects/{project.id}/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["project"]["id"] == project.id
    assert body["summary"]["metric_label"] == "prototype_indicator"
    assert body["metrics"]["metric_label"] == "prototype_indicator"
    assert body["provenance"]["evidence_level"] == "simulation"
    assert body["provenance"]["can_make_ecological_claims"] is False
    assert body["provenance"]["next_required_proof"]
    assert body["sites"][0]["project_id"] == project.id
    assert body["recent_detections"]
    assert body["job_counts_by_status"]["completed"] >= 1
    assert body["top_species"][0]["label"] == "American Robin"


def test_project_readiness_reports_real_vs_simulated_evidence(client, db_session):
    from scripts.simulate_central_park_pilot import PROJECT_EXTERNAL_ID, simulate

    simulate(db_session, recordings_per_site=2, seed_value=7)
    project = db_session.scalar(select(Project).where(Project.external_id == PROJECT_EXTERNAL_ID))

    response = client.get(f"/projects/{project.id}/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_level"] == "simulation"
    assert body["simulation_only"] is True
    assert body["can_make_ecological_claims"] is False
    assert body["claim_status"] == "Demo rehearsal only"
    assert "Do not present" in body["disclaimer"]
    assert body["counts"]["sites"] == 5
    assert body["counts"]["audio_files"] == 10
    assert body["counts"]["simulated_outputs"] == 10
    assert body["counts"]["real_birdnet_outputs"] == 0
    assert body["review_counts"]["confirmed"] > 0
    assert "Simulation rehearsal only" in body["message"]


def test_project_evidence_package_and_markdown_export(client, db_session):
    from scripts.simulate_central_park_pilot import PROJECT_EXTERNAL_ID, simulate

    simulate(db_session, recordings_per_site=2, seed_value=7)
    project = db_session.scalar(select(Project).where(Project.external_id == PROJECT_EXTERNAL_ID))

    package_response = client.get(f"/projects/{project.id}/evidence-package")
    markdown_response = client.get(f"/exports/evidence-package.md?project_id={project.id}")

    assert package_response.status_code == 200
    package = package_response.json()
    assert package["readiness"]["evidence_level"] == "simulation"
    assert package["summary"]["site_count"] == 5
    assert package["top_species"]
    assert "simulated pilot rehearsal" in package["partner_language"]
    assert markdown_response.status_code == 200
    assert "text/markdown" in markdown_response.headers["content-type"]
    assert "# Central Park Acoustic Biodiversity Pilot Simulation Evidence Package" in markdown_response.text
    assert "Recommended Next Actions" in markdown_response.text


def test_geojson_exports_are_map_ready(client, db_session):
    from scripts.simulate_central_park_pilot import PROJECT_EXTERNAL_ID, simulate

    simulate(db_session, recordings_per_site=1, seed_value=9)
    project = db_session.scalar(select(Project).where(Project.external_id == PROJECT_EXTERNAL_ID))

    sites_response = client.get(f"/exports/sites.geojson?project_id={project.id}")
    detections_response = client.get(f"/exports/detections.geojson?project_id={project.id}")

    assert sites_response.status_code == 200
    assert "application/geo+json" in sites_response.headers["content-type"]
    sites_body = json.loads(sites_response.text)
    assert sites_body["type"] == "FeatureCollection"
    assert len(sites_body["features"]) == 5
    assert sites_body["features"][0]["geometry"]["type"] == "Point"
    assert detections_response.status_code == 200
    detections_body = json.loads(detections_response.text)
    assert detections_body["features"]
    assert {"label", "confidence", "review_status", "evidence_level", "claim_status"} <= set(
        detections_body["features"][0]["properties"]
    )
    assert detections_body["features"][0]["properties"]["evidence_level"] == "simulation"


def test_biodiversity_metrics_and_csv_exports(client, db_session):
    project = db_session.scalar(select(Project))
    site = db_session.scalar(select(Site))
    upload_response = client.post(
        "/audio-files/upload",
        data={"site_id": site.id, "duration_seconds": "3600"},
        files={"file": ("metrics.wav", tiny_wav_bytes(), "audio/wav")},
    )
    audio_file_id = upload_response.json()["id"]
    job = db_session.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))
    client.post(f"/processing-jobs/{job.id}/run-mock")

    metrics = client.get(f"/projects/{project.id}/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["recording_hours"] == 1.0
    assert metrics.json()["species_richness"] >= 0
    assert metrics.json()["metric_label"] == "prototype_indicator"

    csv_response = client.get(f"/exports/detections.csv?project_id={project.id}")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "evidence_level" in csv_response.text


def test_create_project_endpoint(client, db_session):
    organization = db_session.scalar(select(Organization))

    response = client.post(
        "/projects",
        json={
            "organization_id": organization.id,
            "name": "Wetland Recovery Pilot",
            "description": "New field project created from the UI.",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Wetland Recovery Pilot"
    assert response.json()["status"] == "active"


def test_create_site_endpoint(client, db_session):
    project = db_session.scalar(select(Project))

    response = client.post(
        "/sites",
        json={
            "project_id": project.id,
            "name": "North Meadow",
            "habitat_type": "restored grassland",
            "latitude": 40.72,
            "longitude": -74.01,
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "North Meadow"
    site = db_session.get(Site, response.json()["id"])
    assert site.location_geom_wkt == "POINT(-74.01 40.72)"


def test_scoped_filters_and_detail_endpoints(client, db_session):
    project = db_session.scalar(select(Project))
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="filters.wav", storage_uri="s3://example/filters.wav")
    db_session.add(audio_file)
    db_session.commit()
    job = ProcessingJob(audio_file_id=audio_file.id)
    db_session.add(job)
    db_session.commit()
    client.post(f"/processing-jobs/{job.id}/run-mock")

    assert client.get(f"/projects/{project.id}").json()["id"] == project.id
    assert client.get(f"/sites?project_id={project.id}").json()[0]["id"] == site.id
    assert client.get(f"/sites/{site.id}").json()["id"] == site.id
    assert client.get(f"/audio-files?site_id={site.id}").json()[0]["site_id"] == site.id
    assert client.get(f"/audio-files/{audio_file.id}").json()["id"] == audio_file.id
    assert client.get(f"/processing-jobs?audio_file_id={audio_file.id}").json()[0]["audio_file_id"] == audio_file.id
    assert client.get(f"/processing-jobs/{job.id}").json()["id"] == job.id
    assert client.get(f"/detections?project_id={project.id}&detection_type=species").json()[0]["detection_type"] == "species"


def test_detection_review_update(client, db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="review.wav", storage_uri="s3://example/review.wav")
    db_session.add(audio_file)
    db_session.commit()
    job = ProcessingJob(audio_file_id=audio_file.id)
    db_session.add(job)
    db_session.commit()
    client.post(f"/processing-jobs/{job.id}/run-mock")
    detection = db_session.scalar(select(Detection).where(Detection.audio_file_id == audio_file.id))

    response = client.patch(f"/detections/{detection.id}", json={"review_status": "confirmed"})

    assert response.status_code == 200
    assert response.json()["review_status"] == "confirmed"


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
    detail_response = client.get(f"/reports/{create_response.json()['id']}")
    assert detail_response.status_code == 200


def test_tnfd_and_esrs_compliance_exports(client, db_session):
    project = db_session.scalar(select(Project))
    site = db_session.scalar(select(Site))

    tnfd_res = client.get(f"/exports/tnfd-biodiversity.json?project_id={project.id}")
    assert tnfd_res.status_code == 200
    assert "TNFD" in tnfd_res.json()["framework"]
    assert "monitored_sites_count" in tnfd_res.json()["indicators"]

    esrs_res = client.get(f"/exports/esrs-compliance.json?project_id={project.id}")
    assert esrs_res.status_code == 200
    assert "ESRS E4" in esrs_res.json()["standard"]


def test_auth_token_and_api_key_validation():
    from backend.app.api.auth import create_dev_token, verify_dev_token

    token = create_dev_token("usr_123", "alice@example.com", "admin")
    principal = verify_dev_token(token)
    assert principal is not None
    assert principal.email == "alice@example.com"
    assert principal.role == "admin"

    bad = verify_dev_token("invalid:token:format")
    assert bad is None


def test_waveform_peaks_extraction():
    from backend.app.services.audio_storage import extract_waveform_peaks

    # Tiny WAV bytes test
    peaks = extract_waveform_peaks(tiny_wav_bytes(), 50)
    assert len(peaks) == 50
    assert all(0.0 <= p <= 1.0 for p in peaks)

