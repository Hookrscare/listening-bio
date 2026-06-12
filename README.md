# AI Biodiversity Backend

Backend foundation for the first MVP slice: project, site, WAV upload, local audio storage, processing jobs, BirdNET-ready adapter processing, normalized detections, seed data, CSV exports, and prototype dashboard summaries.
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

Open `http://127.0.0.1:8000/app`. The UI connects to the FastAPI backend at `http://127.0.0.1:8000` and supports project overview, habitat mapping, WAV/audio metadata intake, queued processing, detection review, raw model traceability, CSV export, and report shell creation.

Use the Survey Intake file picker to upload a local `.wav`; this queues a `birdnet_analysis` job. Without a configured BirdNET command, the adapter stores clearly marked simulated BirdNET-style detections so the workflow remains testable.

## BirdNET Adapter

The app is ready for a real BirdNET command without changing the API or database architecture. Set `BIRDNET_COMMAND` to a command template that accepts `{input}` and writes outputs to `{output_dir}`:

```bash
make birdnet-install
make birdnet-check
export BIRDNET_COMMAND='.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}'
make birdnet-verify
```

Until that variable is configured, `birdnet_analysis` jobs run in `simulated` mode and write the mode into `raw_model_outputs.payload`. Check `GET /integrations/birdnet/status` before claiming real model output. See [docs/birdnet-integration.md](docs/birdnet-integration.md).

## Useful Endpoints

- `GET /health`
- `GET /integrations/birdnet/status`
- `GET /organizations`
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/metrics`
- `GET /projects/{project_id}/dashboard`
- `GET /sites`
- `POST /sites`
- `GET /sites/{site_id}`
- `POST /audio-files`
- `POST /audio-files/upload`
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
- `GET /exports/detections.csv?project_id={project_id}`
- `GET /exports/sites.csv?project_id={project_id}`
- `GET /exports/audio-files.csv?project_id={project_id}`

## Worker

Queued mock and BirdNET adapter jobs can be processed without the API endpoint:

```bash
make migrate
make seed
python -m backend.app.workers.run_pending_jobs --limit 10
```

For local SQLite development without Docker, use `make dev-db` instead of `make migrate && make seed`.

The worker dispatches `mock_audio_analysis` and `birdnet_analysis` jobs.

## Current Boundary

This is a working local MVP demo with a polished frontend, real WAV upload, local file storage, CSV export, and a BirdNET-ready processing boundary. Real BirdNET installation, YAMNet adapters, authentication, PDF export, production deployment, and scientifically validated biodiversity scoring are intentionally outside this pass.
