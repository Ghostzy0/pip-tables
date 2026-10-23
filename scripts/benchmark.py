"""Synthetic one-million-row/20-column bounded local measurement."""
import json
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pip_tables.engine import Project

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / ".local-evidence" / "benchmark.json"
with tempfile.TemporaryDirectory(prefix="tables-benchmark-") as directory:
    root = Path(directory)
    data = root / "synthetic.parquet"
    db = duckdb.connect(config={"threads": "2", "memory_limit": "512MB", "autoload_known_extensions": "false", "autoinstall_known_extensions": "false"})
    columns = ["i AS id"] + [f"CASE WHEN i%3=0 THEN NULL ELSE i*{n} END AS value_{n}" for n in range(1,20)]
    db.execute("COPY (SELECT " + ",".join(columns) + " FROM range(1000000) t(i)) TO ? (FORMAT PARQUET)", [str(data)])
    db.close()
    p = Project.create(root / "project")
    start = time.monotonic()
    name = p.import_file(data)
    imported = time.monotonic()-start
    start = time.monotonic()
    result = p.query(f'SELECT COUNT(*) AS rows, SUM(id) AS sum_id, COUNT(value_1) AS present FROM "{name}"')
    assert result.rows == [(1_000_000, 499_999_500_000, 666_666)], result.rows
    summary = time.monotonic()-start
    start = time.monotonic()
    preview = p.query(f'SELECT * FROM "{name}" ORDER BY id')
    assert preview.total == 1_000_000 and len(preview.rows) == 1000 and len(preview.columns) == 20
    elapsed = time.monotonic()-start
    start = time.monotonic()
    exported = p.export(f'SELECT * FROM "{name}" ORDER BY id', root / "result.parquet", "parquet")
    assert exported == 1_000_000
    export_seconds = time.monotonic()-start
    usage = resource.getrusage(resource.RUSAGE_SELF)
    p.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"host": platform.platform(), "python": platform.python_version(), "duckdb": duckdb.__version__, "rows": 1_000_000, "columns":20, "input_bytes": data.stat().st_size, "import_seconds":imported,"oracle_summary_seconds":summary,"preview_seconds":elapsed,"preview_rows":len(preview.rows),"export_seconds":export_seconds,"export_rows":exported,"process_peak_rss_bytes":usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss*1024,"process_user_cpu_seconds":usage.ru_utime,"process_system_cpu_seconds":usage.ru_stime,"energy":"not measured","scope":"source synthetic batch, not native idle or energy certification","sum_id":499_999_500_000,"non_null_value_1":666_666},indent=2)+"\n")
    print(out.read_text())
