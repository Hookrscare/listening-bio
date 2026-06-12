import argparse
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import ProcessingJob, Site
from database.seed.seed_data import seed
from scripts.create_sample_wav import create_sample_wav


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real BirdNET command through the BioSignal pipeline.")
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--duration-seconds", type=float, default=6.0)
    args = parser.parse_args()

    if not os.environ.get("BIRDNET_COMMAND"):
        print("BIRDNET_COMMAND is not set, so the app would run in simulated mode.")
        print("Example:")
        print("export BIRDNET_COMMAND='python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}'")
        return 2

    if args.audio is None:
        stamp = int(time.time())
        run_id = uuid.uuid4().hex[:8]
        args.audio = Path(f"work/sample-birdnet-{stamp}-{run_id}.wav")
        frequency = 180.0 + (int(run_id, 16) % 90_000) / 1_000
        create_sample_wav(args.audio, seconds=args.duration_seconds, frequency=frequency)
        print(f"Generated synthetic WAV at {args.audio}. Use real field audio for meaningful species detections.")
    elif not args.audio.exists():
        create_sample_wav(args.audio, seconds=args.duration_seconds)
        print(f"Generated synthetic WAV at {args.audio}. Use real field audio for meaningful species detections.")

    with SessionLocal() as db:
        seed(db)
        site = db.scalar(select(Site).order_by(Site.created_at.asc()))
        if site is None:
            print("No site available after seeding.")
            return 1
        site_id = site.id

    client = TestClient(app)
    with args.audio.open("rb") as handle:
        upload = client.post(
            "/audio-files/upload",
            data={"site_id": site_id, "duration_seconds": str(args.duration_seconds)},
            files={"file": (args.audio.name, handle, "audio/wav")},
        )
    if upload.status_code != 201:
        print(f"Upload failed: {upload.status_code} {upload.text}")
        return 1

    audio_file_id = upload.json()["id"]
    with SessionLocal() as db:
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))
        if job is None:
            print("No processing job created.")
            return 1
        job_id = job.id

    run = client.post(f"/processing-jobs/{job_id}/run-mock")
    if run.status_code != 200:
        print(f"Processing failed: {run.status_code} {run.text}")
        return 1

    job_body = run.json()
    detections = client.get(f"/detections?audio_file_id={audio_file_id}").json()
    raw_outputs = client.get("/raw-model-outputs").json()
    raw = next((item for item in raw_outputs if item["audio_file_id"] == audio_file_id), None)
    mode = raw["payload"]["mode"] if raw else "missing"

    print(f"Job status: {job_body['status']}")
    print(f"BirdNET mode: {mode}")
    print(f"Detection count: {len(detections)}")
    if detections:
        for detection in detections[:10]:
            print(f"- {detection['label']} ({detection['confidence']:.3f})")
    else:
        print("No species detections were produced. That can be normal for synthetic or quiet audio.")

    if job_body["status"] != "completed" or mode not in {"configured", "configured_no_detections"}:
        print("Real BirdNET command did not complete in configured mode.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
