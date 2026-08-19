from sqlalchemy import select

from backend.app.models import AudioFile, Detection, ProcessingJob, RawModelOutput, Site
from backend.app.workers.processing_worker import run_pending_jobs


def test_run_pending_jobs_processes_queued_jobs(db_session):
    site = db_session.scalar(select(Site))
    audio_file = AudioFile(site_id=site.id, file_name="worker.wav", storage_uri="s3://example/worker.wav")
    db_session.add(audio_file)
    db_session.flush()
    job = ProcessingJob(audio_file_id=audio_file.id, status="queued")
    db_session.add(job)
    db_session.commit()

    processed = run_pending_jobs(db_session, limit=5)

    assert len(processed) == 1
    assert processed[0].status == "completed"
    assert db_session.scalar(select(RawModelOutput).where(RawModelOutput.audio_file_id == audio_file.id)) is not None
    assert len(db_session.scalars(select(Detection).where(Detection.audio_file_id == audio_file.id)).all()) == 2


def test_run_pending_jobs_respects_limit(db_session):
    site = db_session.scalar(select(Site))
    for index in range(2):
        audio_file = AudioFile(
            site_id=site.id,
            file_name=f"worker-{index}.wav",
            storage_uri=f"s3://example/worker-{index}.wav",
        )
        db_session.add(audio_file)
        db_session.flush()
        db_session.add(ProcessingJob(audio_file_id=audio_file.id, status="queued"))
    db_session.commit()

    processed = run_pending_jobs(db_session, limit=1)

    assert len(processed) == 1
    completed_count = len(db_session.scalars(select(ProcessingJob).where(ProcessingJob.status == "completed")).all())
    queued_count = len(db_session.scalars(select(ProcessingJob).where(ProcessingJob.status == "queued")).all())
    assert completed_count == 1
    assert queued_count == 1


def test_worker_processes_birdnet_jobs(db_session, tmp_path):
    site = db_session.scalar(select(Site))
    wav_path = tmp_path / "birdnet-worker.wav"
    wav_path.write_bytes(
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    audio_file = AudioFile(
        site_id=site.id,
        file_name="birdnet-worker.wav",
        storage_uri=wav_path.as_uri(),
        duration_seconds=20,
    )
    db_session.add(audio_file)
    db_session.flush()
    db_session.add(ProcessingJob(audio_file_id=audio_file.id, status="queued", job_type="birdnet_analysis"))
    db_session.commit()

    processed = run_pending_jobs(db_session, limit=5)

    assert len(processed) == 1
    assert processed[0].status == "completed"
    raw_output = db_session.scalar(select(RawModelOutput).where(RawModelOutput.audio_file_id == audio_file.id))
    assert raw_output.output_format == "birdnet_json"
    assert raw_output.payload["mode"] in {"configured", "configured_no_detections", "simulated"}
