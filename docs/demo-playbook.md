# BioSignal Demo Playbook

## Demo Goal

Prove the core claim:

BioSignal can turn a real wildlife audio recording into auditable candidate biodiversity detections using BirdNET, while preserving source and review context.

## Real Recording Used

- Source: Xeno-canto recording `XC364638`
- Species label on source: American Robin, `Turdus migratorius`
- Recordist: Ted Floyd
- Source page: <https://xeno-canto.org/364638>
- Download: <https://xeno-canto.org/364638/download>
- License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0
- License URL: <https://creativecommons.org/licenses/by-nc-sa/4.0/>
- Location: Colorado near Lafayette, Boulder County, Colorado, United States
- Coordinates: `39.9936, -105.0897`
- Date: `2017-03-28`

## Run The Demo

```bash
make birdnet-install
make birdnet-check
export BIRDNET_COMMAND="$PWD/.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}"
.venv/bin/python scripts/run_real_recording_demo.py
make serve
```

Open:

<http://127.0.0.1:8000/app/>

The script writes a local result artifact to:

`work/demo/XC364638-biosignal-result.json`

## What To Say In The Demo

Use this language:

“This is a real public wildlife recording from Xeno-canto, not synthetic audio. BioSignal converts it to WAV, uploads it through the same API as field recordings, runs the configured BirdNET command, stores raw model output, normalizes detections, and exposes them for human review and CSV export.”

Avoid saying:

- “Scientifically validated biodiversity score”
- “Fully automated ecological survey”
- “Guaranteed species identification”

Say instead:

- “Candidate species detections”
- “Auditable acoustic biodiversity workflow”
- “Prototype indicators for partner validation”

## Current Demo Result

On the local run, BirdNET completed in configured mode and produced candidate detections including American Robin. Some lower-confidence non-target species were also returned, which is exactly why the review workflow matters.

This is a strong proof of the pipeline. It is not yet a validated ecological result.

## Next Proof Step

Record 50 to 100 WAV files across 3 to 5 local sites using a repeatable protocol, run them through BioSignal, review a subset, export CSV, and publish a short pilot report.
