# Pilot Readiness Layer

BioSignal now exposes a readiness layer for each project:

`GET /projects/{project_id}/readiness`

This endpoint is designed for partner and grant demos. It answers a simple question:

Can this project currently support a credible pilot evidence conversation?

## What It Checks

- Project and mapped sites
- Audio survey effort
- Raw model output provenance
- Real BirdNET inference versus simulated output
- Human review evidence
- Export-ready detections

## Evidence Levels

- `simulation`: useful for rehearsal, not ecological claims
- `workflow`: app workflow exists, but real inference evidence is missing
- `real_inference`: at least one configured BirdNET output is present

## Why This Matters

The product should never blur simulation, demo data, and real field evidence. The readiness layer makes that distinction explicit in the API and frontend.

For partner demos, use the readiness panel to say:

“This is what is working today, this is what is simulated, and this is what must be replaced with real field recordings before we make ecological claims.”
