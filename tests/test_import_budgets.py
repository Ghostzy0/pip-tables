import time
import zipfile

import duckdb
import pytest

import pip_tables.engine as engine
from pip_tables.engine import Project


@pytest.fixture
def project(tmp_path):
    item = Project.create(tmp_path / "workspace")
    yield item
    item.close()


@pytest.mark.parametrize(("suffix", "body"), [
    ("csv", "value\n" + "1\n" * 6),
    ("jsonl", ''.join('{"value":1}\n' for _ in range(6))),
])
def test_row_budget_rejects_without_committing(project, tmp_path, monkeypatch, suffix, body):
    monkeypatch.setattr(engine, "_MAX_IMPORT_ROWS", 5)
    source = tmp_path / f"too_many.{suffix}"
    source.write_text(body)
    before = source.read_bytes()
    with pytest.raises(ValueError, match="row limit"):
        project.import_file(source)
    assert source.read_bytes() == before
    assert project.tables() == []
    assert project.history() == []


def test_parquet_row_budget_uses_bounded_scan(project, tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_MAX_IMPORT_ROWS", 5)
    source = tmp_path / "too_many.parquet"
    with duckdb.connect() as conn:
        conn.execute("COPY (SELECT * FROM range(6)) TO ? (FORMAT PARQUET)", [str(source)])
    with pytest.raises(ValueError, match="row limit"):
        project.import_file(source)
    assert project.tables() == []


@pytest.mark.parametrize("member,limit,error", [
    ("xl/sharedStrings.xml", 16 * 1024**2, "shared strings"),
    ("xl/worksheets/sheet1.xml", 128 * 1024**2, "worksheet XML"),
])
def test_xlsx_rejects_declared_expansion_before_openpyxl(tmp_path, monkeypatch, member, limit, error):
    source = tmp_path / "oversized.xlsx"
    source.write_bytes(b"fixture")
    entries = [zipfile.ZipInfo("xl/workbook.xml"), zipfile.ZipInfo(member)]
    entries[1].file_size = limit + 1

    class Archive:
        def __init__(self, *_args, **_kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        def infolist(self): return entries

    monkeypatch.setattr(engine.zipfile, "ZipFile", Archive)
    with pytest.raises(ValueError, match=error):
        Project._source(source, None, "utf-8")


def test_import_deadline_covers_preparation_and_cleans_timer(project, tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_IMPORT_TIMEOUT", 0.02)
    source = tmp_path / "slow.csv"
    source.write_text("value\n1\n")
    original_source = Project._source

    def slow_source(*args, **kwargs):
        time.sleep(0.04)
        return original_source(*args, **kwargs)

    monkeypatch.setattr(Project, "_source", staticmethod(slow_source))
    with pytest.raises(TimeoutError, match="Import timed out"):
        project.import_file(source)
    time.sleep(0.04)
    assert project.tables() == []
    assert project.history() == []
    assert not project._preparing
    assert project._active is None
    assert project._active_stop is None or project._active_stop.is_set()


def test_inspection_deadline_covers_slow_loader_and_cleans_timer(project, tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "_IMPORT_TIMEOUT", 0.02)
    source = tmp_path / "slow.csv"
    source.write_text("value\n1\n")
    original = Project._load_file

    def slow_loader(*args, **kwargs):
        time.sleep(0.04)
        return original(*args, **kwargs)

    monkeypatch.setattr(Project, "_load_file", staticmethod(slow_loader))
    with pytest.raises(TimeoutError, match="inspection timed out"):
        project.inspect_file(source)
    time.sleep(0.04)
    assert project.tables() == []
    assert not project._preparing
    assert project._active is None
    assert project._active_stop is None or project._active_stop.is_set()
