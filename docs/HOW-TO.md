# Analyse a local file with Pip Tables

1. Follow the README source setup or choose the exact experimental release for your Mac. Launch Core or Plus in either appearance.
2. New project → choose an empty folder → Import file. Choose CSV encoding/text handling or an XLSX sheet. Plus shows the inferred first20 rows before you confirm; cancel changes nothing.
3. Select a table and inspect Column profile for missing/distinct/min/max values. Use literal Find or click a column header to sort.
4. Build a query → Summary/Join/Pivot/Change a column type. Check the visible SQL and press CmdReturn. Failed queries preserve the previous successful result.
5. For the synthetic sample, import examples/orders.csv and run:

```sql
SELECT region, SUM(CAST(amount AS DECIMAL(18,2))) AS revenue
FROM orders GROUP BY region ORDER BY region;
```

Expected: North 555.75,South 419.75,West 408.75; grand total 1384.25 over 12 rows with11 non-null amounts. Chart uses the first two columns/50 displayed rows. Exact values remain in Results.

6. Plus Previous/Next rows reruns ordered queries, without adding history entries; volatile values can move. Stop requests cooperative interruption. Do not close until work finishes safely.
7. Export query → choose a NEW CSV/XLSX/JSON/Parquet destination outside the project. Export reruns all matching rows; it does not overwrite existing files.
8. Quit the app. Reopen the whole project folder later for snapshots/history/draft. Keep the original selected files and a separate backup of the project.
