# API Examples

Start the API:

```bash
make dev-db
make serve
```

For PostgreSQL/PostGIS, run `make migrate && make seed` instead of `make dev-db`.

In another terminal, inspect the seed data:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/projects
curl -s http://127.0.0.1:8000/sites
```

Capture the first seeded site id:

```bash
SITE_ID=$(curl -s http://127.0.0.1:8000/sites | python -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
```

Create an audio metadata record. This automatically queues a processing job. The `idempotency_key` prevents duplicate jobs if the same client retries.

```bash
curl -s -X POST http://127.0.0.1:8000/audio-files \
  -H 'Content-Type: application/json' \
  -d "{
    \"site_id\": \"$SITE_ID\",
    \"file_name\": \"morning-survey.wav\",
    \"storage_uri\": \"s3://prototype-audio/morning-survey.wav\",
    \"content_type\": \"audio/wav\",
    \"duration_seconds\": 42.5,
    \"idempotency_key\": \"morning-survey-001\"
  }"
```

Run queued jobs through the worker command:

```bash
python -m backend.app.workers.run_pending_jobs --limit 5
```

Or run one job through the API:

```bash
JOB_ID=$(curl -s http://127.0.0.1:8000/processing-jobs | python -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
curl -s -X POST "http://127.0.0.1:8000/processing-jobs/$JOB_ID/run-mock"
```

Read raw model output, normalized detections, and the prototype project summary:

```bash
curl -s http://127.0.0.1:8000/raw-model-outputs
curl -s http://127.0.0.1:8000/detections

PROJECT_ID=$(curl -s http://127.0.0.1:8000/projects | python -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
curl -s "http://127.0.0.1:8000/projects/$PROJECT_ID/summary"
```

Create a report shell:

```bash
curl -s -X POST http://127.0.0.1:8000/reports \
  -H 'Content-Type: application/json' \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"title\": \"Prototype Biodiversity Summary\",
    \"report_type\": \"prototype_summary\"
  }"
```
