# BirdNET Integration Notes

Listening.bio now has a `birdnet_analysis` job type and adapter boundary. The current local path is intentionally honest:

- uploaded WAV files are stored locally under `work/uploads`
- a `ProcessingJob` is queued with `job_type = birdnet_analysis`
- the worker calls the BirdNET adapter
- if `BIRDNET_COMMAND` is not configured, the adapter writes deterministic simulated species detections
- raw output records include `payload.mode`, so prototype output cannot be confused with real BirdNET output

## Real Runner Contract

Configure `BIRDNET_COMMAND` as a shell command template:

```bash
export BIRDNET_COMMAND='.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}'
```

The adapter replaces:

- `{input}` with the uploaded local WAV path
- `{output_dir}` with a temporary output directory
- `{output}` with a temporary JSON path for custom wrappers
- `{lat}`, `{lon}`, and `{week}` with site/recording metadata when available
- `{min_conf}` with `BIRDNET_MIN_CONFIDENCE`

The adapter parses BirdNET-style CSV/table files, JSON files, or custom JSON wrappers. JSON can be either:

```json
[
  ["Turdus migratorius_American Robin", 0.91]
]
```

or:

```json
[
  {
    "label": "Turdus migratorius_American Robin",
    "confidence": 0.91,
    "start_seconds": 4.0,
    "end_seconds": 7.0
  }
]
```

CSV/table output should include any recognizable combination of:

- `Scientific name` and `Common name`
- `Begin Time (s)` / `End Time (s)` or `Start (s)` / `End (s)`
- `Confidence`, `Score`, or `Probability`

## Status Endpoint

Use this endpoint to verify whether the app is connected to a real runner:

```bash
curl http://127.0.0.1:8000/integrations/birdnet/status
```

When `BIRDNET_COMMAND` is missing, the API returns `mode: simulated`. That path is useful for local demos, but real ecological validation requires a configured BirdNET runner and review by qualified users.

## Local Installation And Verification

Install the optional BirdNET runtime only on machines that need to run inference:

```bash
make birdnet-install
make birdnet-check
export BIRDNET_COMMAND='.venv/bin/python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}'
make birdnet-sample
make birdnet-verify
```

`make birdnet-verify` runs through the Listening.bio upload and processing pipeline. Synthetic audio may produce zero detections; use a real field recording to validate ecological output.

## Source Notes

BirdNET-Analyzer is the intended real species detection engine. Cornell describes it as a tool for large-scale animal sound analysis with batch processing, confidence scoring, spatial filtering, multithreading, and server/API options.

Primary references:

- [Cornell BirdNET-Analyzer](https://birdnet.cornell.edu/analyzer/)
- [BirdNET-Analyzer documentation](https://birdnet-team.github.io/BirdNET-Analyzer/)
- [BirdNET-Analyzer GitHub repository](https://github.com/birdnet-team/BirdNET-Analyzer)
