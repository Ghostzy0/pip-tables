# Verification and limits

23 October 2026, macOS Apple Silicon, CPython 3.13.16, DuckDB1.4.3, PySide6Essentials6.10.2. This file distinguishes tests from native acceptance.

Current source: 57 engine/Qt tests pass, including all Core regressions and Plus import inspection/hash checks, sheet listing, page boundaries/history/reset/failure recovery and all 18  theme contrasts. Source Core/Plus smoke passed. Actual offscreen source renders at900×720,1280×720,1440×900 and import-inspection dialog inspected. These do not certify screen-reader behavior.

Pre-release Core package checkpoint: neutral and Pip actual arm64 packages built; deep/strict ad-hoc signature verification and frozen synthetic smoke passed. Native baseline earlier query/chart/error/profile walkthrough passed. Native Pip folder open, CmdReturn and regional chart passed: North 555.75,South 419.75,West 408.75. Query reported0.015s. Five one-second idle samples showed0.0%ps CPU and about225MiBRSS, cumulativeCPU0.91s unchanged. Short samples on one host are not an energy-efficiency certificate. Native VoiceOver, macOS Reduce Motion toggling and a second Mac remain unverified. No OS setting was changed for this check.

Resource fixes now include512 MB, two threads and no spill native bounded Parquet COPY, cooperative120-second import deadline, explicitone million row import rejection and XLSX expanded256 MiB/sharedstrings16 MiB/worksheet128 MiB preflight caps. Plus packages/clean-clone audit and million-row measurements are still pending at this checkpoint. Final release assets must identify their exact source SHA and checksums. No downloaded binary should be described as notarised or stable.

Queries/profiles use one deadline and bounded previews; export reruns SQL and refuses every existing destination. Spreadsheet formula-like export text is escaped. JSON decimal/date/UUID/binary encode as text/ISO/hex; nonfinite JSON becomes null. Excel wide numbers/nested values are text. Parquet is the typed-roundtrip format. Source inputs are never changed.

Stop is cooperative around Python XLSX parsing; it cannot preempt an openpyxl call in progress. DuckDB limits cover the native engine, not all Python/Qt memory or total persistent project disk. Inspection stages up to 1,000,001 rows and rejects inputs overone million, then returns only 20 rows; temporary storage can be substantial. No process security sandbox or malicious-engine-exploit immunity is claimed. Back up your whole plaintext project folder.

Measured performance fix: the initial million-row × 20-column Parquet export reached its 120-second deadline. Native bounded COPY replaced Python staging. The same fixture then imported in0.249s, summarized in0.0069s, previewed in0.0144s and exported1mrows in0.335s; process peak RSS327122944bytes, CPUuser0.983s/system0.067s. These are source-batch measurements on one Mac; energy unmeasured. Public PR3 contains review and tests. Final rebuilt package checks remain pending.
