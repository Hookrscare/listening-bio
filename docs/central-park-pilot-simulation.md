# Central Park Pilot Simulation

## Purpose

This dataset is a rehearsal asset while partner conversations are underway. It is not real field evidence.

The simulation lets Listening.bio demonstrate the workflow a Central Park partner would see:

`site planning -> audio survey -> BirdNET-like candidate detections -> review -> dashboard -> CSV/report shell`

## Simulated Scope

- 5 habitat sites
- 100 WAV recording records
- 30-day survey window
- BirdNET-style species candidate detections
- Environmental sound-class detections
- Mixed review states: confirmed, rejected, and unreviewed
- Draft partner outreach and report shell

## Sites

- North Woods
- The Ramble
- Jacqueline Kennedy Onassis Reservoir
- Sheep Meadow
- Hallett Nature Sanctuary

## Run It

```bash
.venv/bin/python scripts/simulate_central_park_pilot.py
make serve
```

Open:

<http://127.0.0.1:8000/app/>

Select:

`Central Park Acoustic Biodiversity Pilot Simulation`

## Demo Language

Use:

“This is a simulated Central Park pilot dataset that shows the workflow and expected evidence package. It is designed to rehearse the partner conversation before real field recordings are collected.”

Do not use:

“Central Park biodiversity results”

or:

“Validated Central Park detections”

## What This Helps Prove

- The app can handle a pilot-shaped dataset.
- Partners can understand the site/audio/detection/review/export workflow.
- The dashboard, map, CSV exports, and report shell are ready for real pilot data.
- The project has a concrete implementation path once permission and field recordings are secured.

## What Must Replace It

- Real WAV recordings from approved Central Park sites
- Actual recording protocol
- Real BirdNET inference with date and location context
- Human review by qualified partners or trained reviewers
- A pilot report that clearly separates raw detections, confirmed detections, and prototype indicators
