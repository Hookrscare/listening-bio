import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.models import AudioFile, Detection, ProcessingJob, RawModelOutput, Site
from database.seed.seed_data import seed


DEMO = {
    "recording_id": "XC364638",
    "species": "American Robin",
    "scientific_name": "Turdus migratorius",
    "recordist": "Ted Floyd",
    "source_url": "https://xeno-canto.org/364638",
    "download_url": "https://xeno-canto.org/364638/download",
    "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0",
    "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "location": "Colorado near Lafayette, Boulder County, Colorado, United States",
    "latitude": 39.9936,
    "longitude": -105.0897,
    "recorded_at": "2017-03-28T05:44:00",
    "duration_seconds": 13.2,
}


def download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return
    urllib.request.urlretrieve(url, target)


def convert_to_wav(mp3_path: Path, wav_path: Path) -> None:
    if wav_path.exists() and wav_path.stat().st_size > 0:
        return
    converter = "/usr/bin/afconvert"
    if not Path(converter).exists():
        raise RuntimeError("This demo needs afconvert on macOS to convert the public MP3 sample to WAV.")
    subprocess.run(
        [converter, "-f", "WAVE", "-d", "LEI16@44100", "-c", "1", str(mp3_path), str(wav_path)],
        check=True,
    )


def ensure_demo_site() -> str:
    with SessionLocal() as db:
        seed(db)
        site = db.scalar(select(Site).where(Site.name == "Xeno-canto American Robin Demo"))
        if site is None:
            project_site = db.scalar(select(Site).order_by(Site.created_at.asc()))
            if project_site is None:
                raise RuntimeError("Seed data did not create a project/site.")
            site = Site(
                project_id=project_site.project_id,
                name="Xeno-canto American Robin Demo",
                habitat_type="open woodland / suburban edge",
                latitude=DEMO["latitude"],
                longitude=DEMO["longitude"],
                location_geom_wkt=f"POINT({DEMO['longitude']} {DEMO['latitude']})",
            )
            db.add(site)
            db.commit()
            db.refresh(site)
        return site.id


def main() -> int:
    if not os.environ.get("BIRDNET_COMMAND"):
        print("BIRDNET_COMMAND is required for the real recording demo.")
        print("Example:")
        print("export BIRDNET_COMMAND=\"$PWD/.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}\"")
        return 2

    demo_dir = Path("work/demo")
    mp3_path = demo_dir / "XC364638-american-robin.mp3"
    wav_path = demo_dir / "XC364638-american-robin.wav"
    result_path = demo_dir / "XC364638-biosignal-result.json"

    download_file(DEMO["download_url"], mp3_path)
    convert_to_wav(mp3_path, wav_path)
    site_id = ensure_demo_site()

    client = TestClient(app)
    with wav_path.open("rb") as handle:
        upload = client.post(
            "/audio-files/upload",
            data={
                "site_id": site_id,
                "duration_seconds": str(DEMO["duration_seconds"]),
                "recorded_at": DEMO["recorded_at"],
            },
            files={"file": (wav_path.name, handle, "audio/wav")},
        )
    if upload.status_code != 201:
        print(f"Upload failed: {upload.status_code} {upload.text}")
        return 1

    audio_file_id = upload.json()["id"]
    with SessionLocal() as db:
        audio_file = db.get(AudioFile, audio_file_id)
        if audio_file is None:
            raise RuntimeError("Uploaded audio file was not persisted.")
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.audio_file_id == audio_file_id))
        if job is None:
            raise RuntimeError("No processing job was created for the demo recording.")
        job_id = job.id
        already_completed = job.status == "completed"

    if not already_completed:
        run = client.post(f"/processing-jobs/{job_id}/run-mock")
        if run.status_code != 200:
            print(f"Processing failed: {run.status_code} {run.text}")
            return 1

    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_id)
        raw_output = db.scalar(
            select(RawModelOutput)
            .where(RawModelOutput.audio_file_id == audio_file_id)
            .order_by(RawModelOutput.created_at.desc())
        )
        detections = list(
            db.scalars(select(Detection).where(Detection.audio_file_id == audio_file_id).order_by(Detection.start_seconds))
        )

    result = {
        "source": DEMO,
        "bio_signal": {
            "audio_file_id": audio_file_id,
            "processing_job_id": job_id,
            "job_status": job.status if job else "missing",
            "birdnet_mode": raw_output.payload.get("mode") if raw_output else "missing",
            "detection_count": len(detections),
            "detections": [
                {
                    "label": detection.label,
                    "confidence": detection.confidence,
                    "start_seconds": detection.start_seconds,
                    "end_seconds": detection.end_seconds,
                    "review_status": detection.review_status,
                }
                for detection in detections
            ],
        },
    }
    result_path.write_text(json.dumps(result, indent=2))

    print(f"Source: {DEMO['recording_id']} {DEMO['species']} by {DEMO['recordist']}")
    print(f"License: {DEMO['license']} ({DEMO['license_url']})")
    print(f"Job status: {result['bio_signal']['job_status']}")
    print(f"BirdNET mode: {result['bio_signal']['birdnet_mode']}")
    print(f"Detection count: {len(detections)}")
    for detection in detections[:12]:
        print(f"- {detection.label} ({detection.confidence:.3f}) {detection.start_seconds:.1f}s-{detection.end_seconds:.1f}s")
    print(f"Result artifact: {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
