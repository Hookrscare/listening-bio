# Verification

Use these checks to prove the program works.

## Fast Automated Check

```bash
make test
make smoke
```

`make test` runs the full backend test suite. `make smoke` performs the complete product loop in memory:

1. Health check
2. Create a project
3. Create a site
4. Create audio metadata
5. Upload a WAV file and queue a BirdNET adapter job
6. Create and run a mock processing job
7. Run BirdNET adapter processing
8. Store raw model output and normalized detections
9. Confirm a detection
10. Create a report shell
11. Read the project dashboard aggregate and prototype metrics
12. Export detections as CSV
13. Confirm the frontend and map shell are served at `/app/`

## Manual UI Check

```bash
make dev-db
make serve
```

Open:

```text
http://127.0.0.1:8000/app/
```

Then verify:

- The sidebar says `API online`.
- The proof cards show `Connected`.
- The Map section shows the seeded site marker or the coordinate fallback state.
- Create a project.
- Add a site to that project.
- Upload a WAV file or create an audio metadata record.
- Click `Run queued jobs`.
- Confirm or reject a detection.
- Export detections as CSV.
- Create a report shell.
- Refresh and confirm the counts persist.

## Browser QA

The UI has been checked in Chrome at desktop and mobile widths. Screenshots are written to `work/` during local QA and intentionally ignored by Git.
