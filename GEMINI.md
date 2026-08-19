# GEMINI.md - listening.bio SaaS Project Instructions

Welcome to **listening.bio SaaS** — the AI-powered bioacoustic audio monitoring and biodiversity analytics platform.

This document configures **Gemini CLI** context, guidelines, architectural rules, and project-specific commands for this repository.

---

## 1. Project Overview & Stack Architecture

`listening.bio` is a scalable SaaS platform designed for passive acoustic monitoring (PAM), species detection, and ecological signal analysis.

### Technical Architecture
- **Backend API**: Python 3.11+ / FastAPI (`backend/app/`)
- **Database & ORM**: PostgreSQL with SQLModel / SQLAlchemy & Alembic migrations (`database/`)
- **AI / Model Inference Engine**: BirdNET integration (`backend/app/services/birdnet_processing.py`) & audio processing workers (`backend/app/workers/`)
- **Static Web & Visualization UI**: React 18 + Three.js audio visualizer + Vite + Vitest (`web-static/`)
- **Full-Stack Portal / Website**: Next.js 16 / Vinext + Cloudflare Workers + Drizzle ORM (`website/`)

---

## 2. Directory Structure

```
listening.bio saas/
├── backend/                  # FastAPI Application Core
│   └── app/
│       ├── api/              # API REST Endpoints & Routes
│       ├── db/               # Session management & DB connections
│       ├── models/           # SQLModel DB Entities
│       ├── schemas/          # Pydantic Schemas & DTOs
│       ├── services/         # Audio storage, BirdNET, processing logic
│       └── workers/          # Background worker tasks for audio jobs
├── database/                 # Schema definition & Alembic migrations
│   ├── alembic/              # Migration scripts
│   └── seed/                 # Sample seed data for development
├── docs/                     # Architectural specs, API docs, pilot protocol
├── frontend/                 # Legacy HTML/CSS assets & visualizer scripts
├── outreach/                 # Partner outreach materials & roadmap docs
├── scripts/                  # Helper CLI scripts for testing & simulation
├── tests/                    # Backend Pytest suite
├── web-static/               # Vite + React + Three.js static web app
└── website/                  # Next.js / Vinext web application
```

---

## 3. Essential Commands & Development Workflows

### Gemini CLI Execution
To launch Gemini CLI in this workspace:
```bash
npx gemini
# or using npm script
npm run gemini
```

### Backend (Python / FastAPI)
```bash
# Set up virtual environment and dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
make test
# or
pytest

# Start backend dev server
make serve
# or
uvicorn backend.app.main:app --reload
```

### Frontend / Web Static (React + Vite + Three.js)
```bash
# Development server
npm --prefix web-static run dev

# Run frontend tests
npm --prefix web-static run test

# Build static assets
npm --prefix web-static run build
```

### Website / Next.js Portal
```bash
# Run website tests
npm --prefix website run test

# Build website bundle
npm --prefix website run build
```

---

## 4. Coding Standards & Guidelines for Gemini CLI

1. **Backend & Python Code**:
   - Follow PEP 8 style standards.
   - Use strict type annotations (`typing` module / Pydantic models).
   - Ensure all new API endpoints have corresponding Pytest unit tests in `tests/`.

2. **Frontend & TypeScript Code**:
   - Write modern React components using TypeScript (`.tsx`).
   - Use CSS custom properties (`web-static/src/styles/tokens.css`) for consistent styling.
   - Keep canvas visualizer logic separated from state managers (`ExperienceProvider`, `AudioProvider`).

3. **Database & Migrations**:
   - Any modifications to `backend/app/models/entities.py` require a corresponding Alembic migration script under `database/alembic/versions/`.

---

## 5. Environment Variables & Credentials

Create a local `.env` file based on `.env.example`:
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/listening_bio
BIRDNET_MODEL_PATH=
AUDIO_STORAGE_PATH=./storage/audio
```
