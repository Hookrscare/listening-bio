# Evidence API v1

Listening.bio's first B2B API accepts normalized output from partner-owned or appropriately licensed classifiers. It does not imply that Listening.bio owns or commercially licenses third-party model weights.

## Shipped foundation

- Organization-scoped API keys are stored only as SHA-256 hashes.
- `POST /v1/evidence/model-runs` imports external species detections and retains the submitted raw payload.
- Imports create a completed processing job, normalized detections, model registry entry, and usage event.
- `POST /v1/evidence/detections/{id}/reviews` appends an immutable review event and updates the cached current status.
- `GET /v1/evidence/detections/{id}/reviews` returns the ordered review history.
- Resource queries enforce ownership through audio file, site, project, and organization relationships.
- Reviewer IDs, when supplied, must belong to the API key's organization.

## API key provisioning

Raw API keys must be generated with a cryptographically secure random generator. Store only `hash_api_key(raw_key)` in `api_keys.key_hash`, show the raw key once to the customer, and never log it. Key creation and rotation need an authenticated administrative workflow before public launch.

## Deliberately not claimed

- The API is not yet a scientifically validated evidence standard.
- Imported detections are unreviewed until an authorized reviewer appends a review event.
- Billing is not implemented; `usage_events` is metering evidence only.
- Local uploads remain supported. Direct S3/R2 uploads, malware scanning, retention policies, and object-lock configuration remain infrastructure work.
- Real BirdNET inference remains subject to the model and code licenses applicable to the deployed version and use case.

## Production gates

1. Add authenticated API-key creation, rotation, expiration, scopes, and revocation.
2. Add request idempotency for model-run imports.
3. Configure PostgreSQL/PostGIS and test concurrent review writes against PostgreSQL.
4. Add presigned object uploads with size/type constraints and upload-completion verification.
5. Add rate limits, structured security logs, secret management, backups, and alerting.
6. Version the normalized detection schema and document taxonomy identifiers.
7. Complete privacy, retention, data-processing, and scientific-review policies.
