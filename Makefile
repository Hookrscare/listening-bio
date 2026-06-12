PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: venv install birdnet-install birdnet-check birdnet-sample birdnet-verify test smoke migrate seed dev-db serve frontend worker clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/pip install -e ".[dev]"

birdnet-install: install
	$(BIN)/pip install -e ".[birdnet]"

birdnet-check:
	$(BIN)/python scripts/check_birdnet.py

birdnet-sample:
	$(BIN)/python scripts/create_sample_wav.py work/sample-birdnet.wav

birdnet-verify:
	$(BIN)/python scripts/verify_birdnet_real.py

test:
	$(BIN)/python -m pytest -q

smoke:
	$(BIN)/python scripts/smoke_app.py

migrate:
	$(BIN)/alembic -c database/alembic.ini upgrade head

seed:
	$(BIN)/python -m database.seed.seed_data

dev-db:
	$(BIN)/python scripts/init_dev_db.py

serve:
	$(BIN)/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && ../$(BIN)/python -m http.server 5173

worker:
	$(BIN)/python -m backend.app.workers.run_pending_jobs --limit 10

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache *.egg-info
