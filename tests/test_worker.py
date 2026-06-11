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

