# Pip Tables questions

## What problem does Pip Tables solve?

It lets you inspect local CSV, Excel XLSX, JSON/NDJSON and Parquet data, run visible SQL, profile missing values, make a simple chart and export a result. Projects retain imported snapshots, query history and the editor draft. It runs on your own Mac.

## Which systems are supported?

The experimental package recipe is tested on Apple Silicon macOS 13+ with Python 3.13. Linux source CI checks headless tests and smoke workflows; it does not establish Linux desktop acceptance. Intel Macs, Windows and a second Mac are unverified.

## Does it send my spreadsheets to an AI or server?

Core and Plus contain no provider/account/model/network runtime. They use embedded DuckDB and selected local files. Projects contain plaintext data, paths and query history; back up and protect the whole project folder yourself. Package setup downloads dependencies from PyPI.

## What is the difference between Core and Plus?

Both appearances have the same Core workflow. Plus adds a 20-row/type import inspection, an Excel sheet picker, change detection before import and pages of 1,000 result rows. Neutral uses native system styling; Pip adds original themes and one short optional completion motion. There are four named configurations, one engine and format 2.

## Is this Julius, Duckling or their source code?

No. It is an original MIT application with licensed dependencies and original Pip artwork. Julius is a proprietary behavior reference; a bounded synthetic analysis/chart/CSV-preview workflow was observed. Duckling is a pinned MIT design/workflow reference; its code was not imported. Natural-language analysis and complete vendor parity are not included.

## Can I edit cells or run arbitrary Python?

No cell editor, macros or arbitrary Python/shell execution is included. SQL and deterministic recipes provide read-only transformations over imported tables. Generated SQL remains visible before you run it.

## Are exports identical to the displayed result?

Export reruns the last successful query with all matching rows. Time/random functions can differ. CSV/XLSX formula-like text is escaped; decimal/date/nested values have documented text encodings. Use Parquet for typed roundtrips. Existing files are never replaced.

## What are the limits?

Inputs under2 GB and at mostone million rows; tighter XLSX expanded/shared-string/worksheet caps; previews1,000 rows/512 columns / 8 MiB/1 MiB per cell; default query/profile deadline10 seconds, import/export120 seconds cooperative deadlines. Python parser calls cannot be preempted immediately. Native DuckDB512 MB/2threads/no-spill is not a cap on all Qt/Python memory or total project disk. See README and VERIFICATION.

## Is the package signed and production-ready?

Experimental packages are locally ad-hoc signed, without publisher identity or notarisation. Source setup is available; do not disable macOS security globally. Native VoiceOver, OS Reduce Motion toggling and a second Mac remain unverified. Release notes identify exact source/checksums/evidence; no ratings, download counts or performance guarantees are implied.
