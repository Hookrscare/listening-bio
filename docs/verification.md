# Verification

Use these checks to prove the program works.

## Fast Automated Check

```bash
make test
make smoke
```

`make test` runs the full backend test suite. `make smoke` performs the complete product loop in memory:

1. Health check
2. Seed project/site data
3. Create audio metadata
4. Create and run a mock processing job
5. Store raw model output and normalized detections
6. Confirm a detection
7. Create a report shell
8. Read the project dashboard aggregate
9. Confirm the frontend is served at `/app/`

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
- Create an audio record.
- Click `Run queued jobs`.
- Confirm or reject a detection.
- Create a report shell.
- Refresh and confirm the counts persist.

## Browser QA

The UI has been checked in Chrome at desktop and mobile widths. Screenshots are written to `work/` during local QA and intentionally ignored by Git.

