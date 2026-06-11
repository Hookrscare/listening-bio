PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: venv install test migrate seed serve clean

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

serve:
	$(BIN)/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache *.egg-info

