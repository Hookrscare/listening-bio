from sqlalchemy.exc import OperationalError

from backend.app.workers.run_pending_jobs import main


def test_worker_cli_reports_unready_database(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["run_pending_jobs", "--limit", "1"])

    def raise_unready_database(db, limit):
        raise OperationalError("select 1", {}, Exception("no such table: processing_jobs"))

    monkeypatch.setattr("backend.app.workers.run_pending_jobs.run_pending_jobs", raise_unready_database)

    exit_code = main()

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Database is not ready" in output
    assert "make migrate && make seed" in output
