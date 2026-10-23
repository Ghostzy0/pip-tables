import datetime as dt
import decimal
import threading
import time
import uuid

import pytest

from pip_tables.engine import Project
from pip_tables import engine


@pytest.fixture
def project(tmp_path):
    item = Project.create(tmp_path / "workspace")
    yield item
    item.close()


def test_native_parquet_preserves_typed_and_nested_values(project, tmp_path):
    target = tmp_path / "typed.parquet"
    sql = """SELECT
        7::TINYINT AS tiny,
        12345678901234567890::DECIMAL(20,0) AS precise,
        DATE '2026-10-23' AS day,
        TIMESTAMP '2026-10-23 12:34:56.123456' AS moment,
        UUID 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AS id,
        [1, 2, NULL]::INTEGER[] AS items,
        {'label': 'βeta', 'score': 9}::STRUCT(label VARCHAR, score INTEGER) AS detail,
        MAP(['alpha', 'beta'], [3, 4]) AS metrics,
        from_hex('00ff10') AS payload"""

    assert project.export(sql, target, "parquet") == 1
    imported = project.import_file(target)
    result = project.query(f"SELECT * FROM {imported}")
    assert result.rows == [(
        7,
        decimal.Decimal("12345678901234567890"),
        dt.date(2026, 10, 23),
        dt.datetime(2026, 10, 23, 12, 34, 56, 123456),
        uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
        [1, 2, None],
        {"label": "βeta", "score": 9},
        {"alpha": 3, "beta": 4},
        bytes.fromhex("00ff10"),
    )]
    assert result.types == [
        "TINYINT", "DECIMAL(20,0)", "DATE", "TIMESTAMP", "UUID",
        'INTEGER[]', 'STRUCT("label" VARCHAR, score INTEGER)',
        "MAP(VARCHAR, INTEGER)", "BLOB",
    ]


def test_parquet_executes_volatile_query_once_and_returns_materialized_count(project, tmp_path):
    target = tmp_path / "volatile.parquet"
    # The row count changes on every execution. The count returned by export
    # must describe the same run that produced the file.
    sql = "SELECT i FROM range(100000) t(i) WHERE random() < 0.5"
    written = project.export(sql, target, "parquet")
    imported = project.import_file(target)
    assert written == project.query(f"SELECT count(*) FROM {imported}").rows[0][0]


@pytest.mark.parametrize("sql", [
    "SELECT * FROM read_text('/etc/passwd')",
    "SELECT * FROM read_csv('/etc/passwd')",
    "SELECT * FROM read_parquet('https://127.0.0.1:9/secret.parquet')",
    "SELECT * FROM read_text('/tmp/../etc/passwd')",
    "SELECT * FROM read_text('/private/etc/passwd')",
    "PRAGMA enable_external_access=true",
    "INSTALL httpfs",
    "COPY (SELECT 1) TO '/tmp/pip-parquet-escape.parquet' (FORMAT PARQUET)",
    "SELECT 1; COPY (SELECT 1) TO '/tmp/pip-parquet-escape.parquet' (FORMAT PARQUET)",
    "DELETE FROM _pip_sources",
])
def test_parquet_keeps_untrusted_sql_external_access_disabled(project, tmp_path, sql):
    source = tmp_path / "source.csv"
    source.write_text("v\n1\n", encoding="utf-8")
    project.import_file(source)
    with pytest.raises(ValueError) as caught:
        project.export(sql, tmp_path / "blocked.parquet", "parquet")
    assert "Export failed" in str(caught.value) or "Only one SELECT" in str(caught.value)
    assert not (tmp_path / "blocked.parquet").exists()
    assert not (tmp_path / "pip-parquet-escape.parquet").exists()
    assert project.query("SELECT count(*) FROM source").rows == [(1,)]


def test_parquet_cancel_removes_all_temporary_files(project, tmp_path, monkeypatch):
    active = threading.Event()
    resume = threading.Event()
    original = Project._start_active
    errors = []

    def pause_after_activation(self, conn):
        original(self, conn)
        active.set()
        assert resume.wait(5)

    monkeypatch.setattr(Project, "_start_active", pause_after_activation)
    target = tmp_path / "cancelled.parquet"

    def run_export():
        try:
            project.export("SELECT i FROM range(1000000) t(i)", target, "parquet")
        except BaseException as exc:
            errors.append(exc)

    worker = threading.Thread(target=run_export)
    worker.start()
    assert active.wait(5)
    project.cancel()
    resume.set()
    worker.join(10)

    assert not worker.is_alive()
    assert errors and isinstance(errors[0], (InterruptedError, ValueError))
    assert not target.exists()
    assert not list(tmp_path.glob(".pip-export-*"))
    assert not list(tmp_path.glob("tmp_.pip-export-*"))


def test_parquet_light_export_uses_native_streaming(project, tmp_path):
    fields = ", ".join(f"i + {index} AS c{index}" for index in range(20))
    target = tmp_path / "light.parquet"
    started = time.perf_counter()
    count = project.export(f"SELECT {fields} FROM range(100000) t(i)", target, "parquet")
    elapsed = time.perf_counter() - started
    assert count == 100_000
    assert target.stat().st_size > 0
    # A broad guard catches regressions back to Python row-by-row insertion
    # while retaining enough room for slower CI runners.
    assert elapsed < 10
    assert not list(tmp_path.glob(".pip-export-*"))


def test_parquet_enforces_core_limits_on_export_connection(project, tmp_path, monkeypatch):
    observed = []
    original = Project._apply_limits

    def capture(conn):
        original(conn)
        observed.append(conn.execute(
            "SELECT current_setting('memory_limit'), current_setting('threads'), "
            "current_setting('max_temp_directory_size')"
        ).fetchone())

    monkeypatch.setattr(Project, "_apply_limits", staticmethod(capture))
    assert project.export("SELECT i FROM range(2) t(i)", tmp_path / "limited.parquet", "parquet") == 2
    assert observed
    assert observed[-1][0].endswith("MiB") and float(observed[-1][0].split()[0]) <= 512
    assert observed[-1][1] == 2
    assert observed[-1][2] in {"0B", "0 B", "0 bytes"}


def test_parquet_row_cap_discards_oversized_temporary_result(project, tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_MAX_EXPORT_ROWS", 3)
    target = tmp_path / "too-many.parquet"
    with pytest.raises(ValueError, match="Export exceeds 3 rows"):
        project.export("SELECT i FROM range(4) t(i)", target, "parquet")
    assert not target.exists()
    assert not list(tmp_path.glob(".pip-export-*"))
    assert not list(tmp_path.glob("tmp_.pip-export-*"))
