import argparse

from sqlalchemy.exc import OperationalError

from backend.app.db.session import SessionLocal
from backend.app.workers.processing_worker import run_pending_jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run queued mock audio-processing jobs.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum queued jobs to run.")
    args = parser.parse_args()

    with SessionLocal() as db:
        try:
            jobs = run_pending_jobs(db, limit=args.limit)
        except OperationalError as exc:
            message = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
            print(f"Database is not ready: {message}")
            print("Run migrations and seed data first, for example: make migrate && make seed")
            return 1

    print(f"Processed {len(jobs)} queued job(s).")
    for job in jobs:
        print(f"{job.id} {job.status} audio_file={job.audio_file_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
