from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from backend.app.config import get_settings


def test_alembic_migration_applies_to_test_database(tmp_path, monkeypatch):
    database_path = tmp_path / "alembic.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    config = Config("database/alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    assert "organizations" in inspector.get_table_names()
    assert "processing_jobs" in inspector.get_table_names()
    assert "detections" in inspector.get_table_names()
    assert "api_keys" in inspector.get_table_names()
    assert "review_events" in inspector.get_table_names()
    assert "usage_events" in inspector.get_table_names()

    get_settings.cache_clear()
