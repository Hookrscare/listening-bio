# AI Biodiversity Backend

Backend foundation for the first MVP slice: project, site, audio metadata, mock processing jobs, normalized detections, seed data, and prototype dashboard summaries.
The validated v1 spine is `organization -> project -> site -> audio_file -> processing_job -> raw_model_output -> detection`; grant and partner objects are prototype shells.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d
alembic -c database/alembic.ini upgrade head
python -m database.seed.seed_data
pytest
uvicorn backend.app.main:app --reload
```

The API starts at `http://127.0.0.1:8000`.

If the system `python` command is unavailable, use `python3` or the helper targets:

```bash
make install
make dev-db
make test
make smoke
make serve
make frontend
make worker
```

`make dev-db` creates and seeds the default local SQLite database for quick development. For the intended PostgreSQL/PostGIS path, use Docker Compose plus Alembic migrations.

On macOS, if `git` fails with an Xcode license message, run Apple’s license flow in Terminal before publishing:

```bash
sudo xcodebuild -license
```

To inspect local tool readiness:

```bash
.venv/bin/python scripts/check_python.py
```

See [docs/api-examples.md](docs/api-examples.md) for copy-pasteable curl examples covering the core vertical slice.
See [docs/verification.md](docs/verification.md) for the repeatable proof that the app works.

## Frontend

The first UI lives in `frontend/` and is served by FastAPI:

```bash
make dev-db
make serve
```

Open `http://127.0.0.1:8000/app`. The UI connects to the FastAPI backend at `http://127.0.0.1:8000` and supports project overview, audio metadata intake, queued mock processing, detection review, raw model traceability, and report shell creation.

## Useful Endpoints

- `GET /health`
- `GET /organizations`
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/dashboard`
- `GET /sites`
- `POST /sites`
- `GET /sites/{site_id}`
- `POST /audio-files`
- `GET /audio-files`
- `GET /audio-files/{audio_file_id}`
- `POST /processing-jobs`
- `GET /processing-jobs`
- `GET /processing-jobs/{job_id}`
- `POST /processing-jobs/{job_id}/run-mock`
- `GET /detections`
- `GET /detections/{detection_id}`
- `PATCH /detections/{detection_id}`
- `GET /raw-model-outputs`
- `POST /reports`
- `GET /reports`
- `GET /reports/{report_id}`

## Worker

Queued mock jobs can be processed without the API endpoint:

```bash
make migrate
make seed
python -m backend.app.workers.run_pending_jobs --limit 10
```

For local SQLite development without Docker, use `make dev-db` instead of `make migrate && make seed`.

The worker currently dispatches `mock_audio_analysis` jobs only. This boundary is where BirdNET/YAMNet adapters should plug in later.

## Current Boundary

This is a working local MVP demo with a polished frontend and mock processing. Real BirdNET/YAMNet adapters, authentication, report export, production deployment, and scientifically validated biodiversity scoring are intentionally outside this pass.
