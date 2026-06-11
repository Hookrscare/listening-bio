# BirdNET Integration Notes

BioSignal now has a `birdnet_analysis` job type and adapter boundary. The current local path is intentionally honest:

- uploaded WAV files are stored locally under `work/uploads`
- a `ProcessingJob` is queued with `job_type = birdnet_analysis`
- the worker calls the BirdNET adapter
- if `BIRDNET_COMMAND` is not configured, the adapter writes deterministic simulated species detections
- raw output records include `payload.mode`, so prototype output cannot be confused with real BirdNET output

## Real Runner Contract

Configure `BIRDNET_COMMAND` as a shell command template:

```bash
export BIRDNET_COMMAND='python /path/to/BirdNET-Analyzer/analyze.py --i {input} --o {output}'
```

The adapter replaces:

- `{input}` with the uploaded local WAV path
- `{output}` with a temporary JSON path

The JSON can be either:

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

## Source Notes

BirdNET-Analyzer is the intended real species detection engine. Cornell describes it as a tool for large-scale animal sound analysis with batch processing, confidence scoring, spatial filtering, multithreading, and server/API options.

Primary references:

- [Cornell BirdNET-Analyzer](https://birdnet.cornell.edu/analyzer/)
- [BirdNET-Analyzer documentation](https://birdnet-team.github.io/BirdNET-Analyzer/)
- [BirdNET-Analyzer GitHub repository](https://github.com/birdnet-team/BirdNET-Analyzer)
