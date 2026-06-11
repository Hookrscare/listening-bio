# Implementation Status

## Ready

- FastAPI application shell
- SQLAlchemy models for the MVP foundation tables
- PostgreSQL/PostGIS-oriented schema SQL
- Alembic initial migration
- Idempotent seed script
- Mock processing service that validates an audio metadata record, creates detections, and completes a job
- Raw model output traceability before normalized detections
- Worker boundary for replacing mock processing with real adapters
- Report shell endpoints for prototype summaries
- Local SQLite dev bootstrap for demos when Docker/PostGIS is unavailable
- Static frontend prototype with dashboard, intake, processing, detections, raw-output evidence, and report shells
- Scoped/detail API endpoints, project dashboard aggregate, and detection review mutation
- Backend tests for health, metadata import, seed idempotency, mock processing, summaries, and Alembic configuration

## Deferred

- Frontend
- Authentication and authorization enforcement
- Real audio upload storage
- BirdNET Analyzer integration
- YAMNet integration
- Report file export
- Admin review panel
- Production deployment configuration
