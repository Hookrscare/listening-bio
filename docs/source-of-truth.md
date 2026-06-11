# Source of Truth

This repository currently uses `database/schema.sql` as a provisional schema generated from the attached planning brief.

The original `database_schema_ai_biodiversity.sql` was referenced in the brief but was not present in the local workspace. When that file becomes available, compare it against:

- SQLAlchemy models as the application runtime source of truth
- Alembic migrations as database change history
- `database/schema.sql` as a generated/reference snapshot only
- `database/alembic/versions/0001_initial_foundation.py`
- `backend/app/models/entities.py`

Any differences should be reconciled through a new Alembic migration rather than by rewriting existing migration history. `schema_versions` records this provisional starting point so later reconciliation is explicit.

The validated core spine is `organization -> project -> site -> audio_file -> processing_job -> raw_model_output -> detection`. Grant, partner, research, outreach, reporting, weekly review, and impact tables are prototype shells until workflow evidence proves their shape.

Prototype biodiversity, activity, noise, community-value, and grant-readiness values are indicators only. They are not scientifically validated metrics until calibrated with real pilot data and domain review.
