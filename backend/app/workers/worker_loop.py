import os
import time

from sqlalchemy.exc import OperationalError

from backend.app.db.session import SessionLocal
from backend.app.workers.processing_worker import run_pending_jobs


def main() -> None:
    poll_seconds = max(1, int(os.getenv("WORKER_POLL_SECONDS", "5")))
    batch_size = max(1, int(os.getenv("WORKER_BATCH_SIZE", "5")))

    while True:
        try:
            with SessionLocal() as db:
                jobs = run_pending_jobs(db, limit=batch_size)
            if jobs:
                print(f"Processed {len(jobs)} queued job(s).", flush=True)
        except OperationalError as exc:
            print(f"Database unavailable: {exc}", flush=True)
        except Exception as exc:
            print(f"Worker batch failed: {exc}", flush=True)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
