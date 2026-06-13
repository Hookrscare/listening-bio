# Expert Critique Snapshot

## Scientific And Product Critique

BioSignal has the right workflow spine for an environmental data system:

`Project -> Site -> Audio -> Processing Job -> BirdNET Output -> Normalized Detection -> Review -> Metrics -> Export`

That is a strong MVP foundation. The major risk is no longer whether the software can be built; it is whether BioSignal can produce defensible ecological evidence from real field audio.

The biggest scientific risk is false confidence. BirdNET can produce plausible detections that are wrong, especially with noisy urban audio, short clips, weak microphones, overlapping species, non-bird sounds, and incorrect date/location context. Metrics must stay labeled as prototype indicators until validated against field review or expert annotation.

The project needs a small pilot dataset: 3 to 5 sites, 50 to 100 real recordings, repeatable sampling protocol, BirdNET detections, reviewer validation, CSV export, and a short pilot report.

## Engineering And Demo Critique

The local demo is strong, but partner-pilot readiness still needs hardening.

Key risks:

- BirdNET depends on an external `BIRDNET_COMMAND`, TensorFlow install, cached model files, and expected output formats.
- Jobs currently run inline when the UI calls the processing endpoint, so large WAVs can block a request.
- Upload validation reads the full WAV into memory.
- The UI needs a clearer proof trail showing real BirdNET mode, source recording, model output, and reviewer status.
- Production observability is thin: job duration, model version, file size, retry count, stderr summary, and per-stage timing should be visible.

## Top Actions

1. Run and document real public and field recordings through BirdNET.
2. Add a partner-facing proof panel that says whether the output is simulated or real.
3. Add provenance fields to the demo story: source, license, location, date, model runner, confidence threshold, review status.
4. Replace inline processing with a background worker for longer recordings.
5. Build a repeatable 30-day pilot with real sites, real audio, CSV exports, maps, and a reviewer-validated summary.
