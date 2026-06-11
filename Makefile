PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: venv install test migrate seed dev-db serve worker clean

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(BIN)/pip install -e ".[dev]"

test:
	$(BIN)/python -m pytest -q

migrate:
	$(BIN)/alembic -c database/alembic.ini upgrade head

seed:
	$(BIN)/python -m database.seed.seed_data

dev-db:
	$(BIN)/python scripts/init_dev_db.py

serve:
	$(BIN)/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

worker:
	$(BIN)/python -m backend.app.workers.run_pending_jobs --limit 10

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache *.egg-info
