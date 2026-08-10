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

The dashboard and exports include evidence provenance fields that separate `workflow`, `simulation`, and `real_inference` states. Use those labels when speaking with partners: simulated pilot data is useful for rehearsal, but only configured BirdNET output from real WAV recordings should be treated as ecological evidence.

The command center keeps this boundary visible in a persistent evidence gate. Simulation projects display an amber rehearsal warning, real inference projects display their review requirement, and ecological claim eligibility remains disabled until the evidence contract records sufficient reviewed real output.

The first partner-facing pilot page is available at `http://127.0.0.1:8000/app/partners.html`.

## BirdNET Adapter

The app is ready for a real BirdNET command without changing the API or database architecture. Set `BIRDNET_COMMAND` to a command template that accepts `{input}` and writes outputs to `{output_dir}`:

```bash
make birdnet-install
make birdnet-check
export BIRDNET_COMMAND='.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}'
make birdnet-verify
```

Until that variable is configured, `birdnet_analysis` jobs run in `simulated` mode and write the mode into `raw_model_outputs.payload`. Check `GET /integrations/birdnet/status` before claiming real model output. See [docs/birdnet-integration.md](docs/birdnet-integration.md).

To run a real public wildlife recording through the full Listening.bio pipeline:

```bash
export BIRDNET_COMMAND="$PWD/.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}"
.venv/bin/python scripts/run_real_recording_demo.py
```

The demo uses Xeno-canto `XC364638`, an American Robin recording by Ted Floyd licensed under Creative Commons BY-NC-SA 4.0. See [docs/demo-playbook.md](docs/demo-playbook.md).

## Central Park Pilot Simulation

While real partner permission and recordings are pending, load a clearly marked simulated Central Park pilot dataset:

```bash
make simulate-pilot
make serve
```

Open `http://127.0.0.1:8000/app/` and select `Central Park Acoustic Biodiversity Pilot Simulation`. This creates 5 simulated sites, 100 audio records, BirdNET-like candidate detections, review states, a report shell, and partner/outreach artifacts. See [docs/central-park-pilot-simulation.md](docs/central-park-pilot-simulation.md).

## Partnership and Funding Package

- [Public-data validation registry](docs/public-data-validation.md)
- [Partner outreach email drafts](docs/partner-outreach-drafts.md)
- [Grant strategy and application draft](docs/grant-strategy-and-draft.md)
- [Send-ready outreach and current micro-grant application](outreach/)

The verified real-audio demo processed Xeno-canto `XC364638` in configured BirdNET mode and wrote its auditable result to `work/demo/XC364638-listening-bio-result.json`. The outreach drafts have not been sent, and grant eligibility still depends on an appropriate university, nonprofit, public-agency, land-trust, or incorporated small-business applicant.

## Useful Endpoints

- `GET /health`
- `GET /integrations/birdnet/status`
- `GET /organizations`
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/metrics`
- `GET /projects/{project_id}/dashboard`
- `GET /projects/{project_id}/readiness`
- `GET /projects/{project_id}/evidence-package`
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
- `POST /processing-jobs/{job_id}/run`
- `POST /processing-jobs/{job_id}/run-mock`
- `GET /detections`
- `GET /detections/{detection_id}`
- `PATCH /detections/{detection_id}`
- `GET /raw-model-outputs?project_id={project_id}`
- `POST /reports`
- `GET /reports`
- `GET /reports/{report_id}`
- `GET /exports/detections.csv?project_id={project_id}`
- `GET /exports/detections.geojson?project_id={project_id}`
- `GET /exports/sites.csv?project_id={project_id}`
- `GET /exports/sites.geojson?project_id={project_id}`
- `GET /exports/audio-files.csv?project_id={project_id}`
- `GET /exports/evidence-package.md?project_id={project_id}`
- `POST /v1/evidence/model-runs` (`X-API-Key` required)
- `POST /v1/evidence/detections/{detection_id}/reviews` (`X-API-Key` required)
- `GET /v1/evidence/detections/{detection_id}/reviews` (`X-API-Key` required)

The Evidence API accepts partner-generated model output, retains raw provenance, meters imports, and records reviews as an append-only history. Only API-key hashes are stored. See [docs/evidence-api-v1.md](docs/evidence-api-v1.md) for its security boundary and production gates.

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

This is a working MVP foundation with a polished frontend, real WAV upload, local file storage, CSV export, a BirdNET-ready processing boundary, and an organization-scoped Evidence API. Hosted object storage, end-user authentication, API-key administration, billing, PDF export, production deployment, and scientifically validated biodiversity scoring are not yet complete.
