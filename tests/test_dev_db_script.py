from scripts.init_dev_db import main


def test_init_dev_db_refuses_non_sqlite(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/example")
    from backend.app.config import get_settings

    get_settings.cache_clear()
    try:
        exit_code = main()
    finally:
        get_settings.cache_clear()

    assert exit_code == 1
    assert "use Alembic migrations" in capsys.readouterr().out

