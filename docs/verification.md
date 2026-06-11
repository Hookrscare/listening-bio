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
5. Create and run a mock processing job
6. Store raw model output and normalized detections
7. Confirm a detection
8. Create a report shell
9. Read the project dashboard aggregate
10. Confirm the frontend is served at `/app/`

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
- Create a project.
- Add a site to that project.
- Create an audio record.
- Click `Run queued jobs`.
- Confirm or reject a detection.
- Create a report shell.
- Refresh and confirm the counts persist.

## Browser QA

The UI has been checked in Chrome at desktop and mobile widths. Screenshots are written to `work/` during local QA and intentionally ignored by Git.
