import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.config import get_settings
from backend.app.models import Base
from database.seed.seed_data import seed


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    if engine.dialect.name != "sqlite":
        print(f"Refusing to create tables directly for {engine.dialect.name}; use Alembic migrations instead.")
        return 1

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as db:
        ids = seed(db)

    print(f"SQLite dev database ready at {settings.database_url}")
    print(f"Seed data ready: {ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
