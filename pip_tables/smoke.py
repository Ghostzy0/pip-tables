"""Explicit synthetic verification for both source and frozen executable."""
import json
import tempfile
from decimal import Decimal
from pathlib import Path

from . import __version__
from .engine import Project


def run(destination: Path, edition: str, enhanced=False):
    with tempfile.TemporaryDirectory(prefix="pip-tables-smoke-") as temp:
        root = Path(temp)
        source = root / "sales.csv"
        source.write_text("region,amount\nNorth,0.10\nNorth,0.20\nSouth,2.05\nSouth,\n", encoding="utf-8")
        project = Project.create(root / "project")
        if enhanced:
            preview = project.inspect_file(source)
            assert preview["total"] == 4 and len(preview["rows"]) == 4
            assert project.tables() == []
            table = project.import_file(source, expected_fingerprint=preview["fingerprint"])
        else:
            table = project.import_file(source)
        sql = f'SELECT region, SUM(CAST(amount AS DECIMAL(18,2))) AS total FROM "{table}" GROUP BY region ORDER BY region'
        result = project.query(sql)
        assert result.rows == [("North", Decimal("0.30")), ("South", Decimal("2.05"))], result.rows
        project.save_draft(sql)
        rows = project.export(sql, root / "export.parquet", "parquet")
        assert rows == 2
        project.close()
        reopened = Project(root / "project")
        assert reopened.draft == sql
        imported = reopened.import_file(root / "export.parquet")
        assert reopened.query(f'SELECT * FROM "{imported}" ORDER BY region').rows == result.rows
        blocked = []
        for query in ["DROP TABLE sales", "SELECT * FROM read_csv('/etc/passwd')", "SELECT 1; SELECT 2"]:
            try:
                reopened.query(query)
            except Exception:
                blocked.append(query)
        assert len(blocked) == 3
        if enhanced:
            before = len(reopened.history())
            page = reopened.query("SELECT i FROM range(2101) AS data(i) ORDER BY i", offset=2000, record_history=False)
            assert len(page.rows) == 101 and page.rows[0] == (2000,) and page.total == 2101
            assert len(reopened.history()) == before
        reopened.close()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"version": "0.2.0a1" if enhanced else __version__, "edition": edition, "enhanced": enhanced, "decimal_oracle": "0.30 + 2.05 = 2.35", "reopen": True, "parquet_roundtrip": True, "hostile_queries_blocked": len(blocked)}, indent=2)+"\n")
