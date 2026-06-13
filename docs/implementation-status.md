# Implementation Status

## Ready

- FastAPI application shell
- SQLAlchemy models for the MVP foundation tables
- PostgreSQL/PostGIS-oriented schema SQL
- Alembic initial migration
- Idempotent seed script
- WAV upload endpoint and local file storage
- Mock processing service that validates an audio metadata record, creates detections, and completes a job
- BirdNET adapter job type with traceable raw output and normalized species detections
- Raw model output traceability before normalized detections
- Worker boundary for mock and BirdNET adapter processing
- Report shell endpoints for prototype summaries
- CSV exports for detections, sites, and audio files
- Prototype biodiversity metrics for recording hours, species richness, detections per hour, confirmed detection percent, and Shannon diversity
- Local SQLite dev bootstrap for demos when Docker/PostGIS is unavailable
- Static frontend prototype with dashboard, habitat map, WAV intake, processing, detections, raw-output evidence, CSV export, and report shells
- Partner-facing pilot page for collaboration conversations
- Scoped/detail API endpoints, project dashboard aggregate, and detection review mutation
- Backend tests for health, metadata import, seed idempotency, mock processing, summaries, and Alembic configuration
- Real public recording demo script using Xeno-canto `XC364638`

## Deferred

- Authentication and authorization enforcement
- Production BirdNET runner tuning and pilot-scale validation
- YAMNet integration
- PDF report file export
- Admin review panel
- Production deployment configuration
