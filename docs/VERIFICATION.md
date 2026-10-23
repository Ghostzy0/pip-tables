# Verification and limits

23 October 2026, macOS Apple Silicon, CPython 3.13.16, DuckDB1.4.3, PySide6Essentials6.10.2. This file distinguishes tests from native acceptance.

Current source: 57 engine/Qt tests pass, including all Core regressions and Plus import inspection/hash checks, sheet listing, page boundaries/history/reset/failure recovery and all 18  theme contrasts. Source Core/Plus smoke passed. Actual offscreen source renders at900×720,1280×720,1440×900 and import-inspection dialog inspected. These do not certify screen-reader behavior.

Pre-release Core package checkpoint: neutral and Pip actual arm64 packages built; deep/strict ad-hoc signature verification and frozen synthetic smoke passed. Native baseline earlier query/chart/error/profile walkthrough passed. Native Pip folder open, CmdReturn and regional chart passed: North 555.75,South 419.75,West 408.75. Query reported0.015s. Five one-second idle samples showed0.0%ps CPU and about225MiBRSS, cumulativeCPU0.91s unchanged. Short samples on one host are not an energy-efficiency certificate. Native VoiceOver, macOS Reduce Motion toggling and a second Mac remain unverified. No OS setting was changed for this check.

Resource fixes now include512 MB, two threads and no spill native bounded Parquet COPY, cooperative120-second import deadline, explicitone million row import rejection and XLSX expanded256 MiB/sharedstrings16 MiB/worksheet128 MiB preflight caps. The three primary custom packages and the legacy neutral Workbench Core package were built from clean public commit `9af81fa3ef9b1bdcd4bddb251a3a557e0305182d`; strict ad-hoc signatures and each packaged synthetic smoke passed. Independent final package review found no high/medium issue in its bounded static/package scope. Each bundle includes 83 Mach-O files and 170 licence files, with no unexpected absolute library dependency. Source tests and frozen smoke do not certify every native interaction. Final release assets identify their exact source SHA and checksums. No downloaded binary should be described as notarised or stable.

Queries/profiles use one deadline and bounded previews; export reruns SQL and refuses every existing destination. Spreadsheet formula-like export text is escaped. JSON decimal/date/UUID/binary encode as text/ISO/hex; nonfinite JSON becomes null. Excel wide numbers/nested values are text. Parquet is the typed-roundtrip format. Source inputs are never changed.

Stop is cooperative around Python XLSX parsing; it cannot preempt an openpyxl call in progress. DuckDB limits cover the native engine, not all Python/Qt memory or total persistent project disk. Inspection stages up to 1,000,001 rows and rejects inputs overone million, then returns only 20 rows; temporary storage can be substantial. No process security sandbox or malicious-engine-exploit immunity is claimed. Back up your whole plaintext project folder.

Measured performance fix: the initial million-row × 20-column Parquet export reached its 120-second deadline. Native bounded COPY replaced Python staging. The same fixture then imported in0.249s, summarized in0.0069s, previewed in0.0144s and exported1mrows in0.335s; process peak RSS327122944bytes, CPUuser0.983s/system0.067s. These are source-batch measurements on one Mac; energy unmeasured. Public PR3 contains review and tests. Final clean-clone package checks passed. A separate final clean-clone batch measured the same 1,000,000-row × 20-column, 55,499,661-byte Parquet input: import0.287051s, summary0.0076965s, preview0.016478s, export0.349894s; peakRSS325009408bytes, CPUuser1.076129s/system0.080761s. These measurements cover one source batch on one macOS27.0.1arm64 host, not native UI energy use.


The four primary editions span two repositories:

| Edition | Repository | Workflow |
| --- | --- | --- |
| Neutral Core | [pip-tables-replica](https://github.com/Ghostzy0/pip-tables-replica) | Original partial Julius-style conversation replica, explicit SQL/recipes |
| Pip Core | [pip-tables](https://github.com/Ghostzy0/pip-tables) | Custom workbench with Pip appearance |
| Neutral Plus | pip-tables | Custom workbench with import inspection, sheet picker and pages |
| Pip Plus | pip-tables | Custom Plus workbench with Pip appearance |

The neutral Workbench Core launcher remains available as a compatible source configuration and was also built and smoke-tested. It is not the Julius-style replica. No edition includes an arbitrary language model or claims complete Julius parity.

Final native package check on macOS27.0.1arm64, source9af81fa: Pip Plus created a project, inspected the selected synthetic CSV (12 rows/6 columns), imported it, ran `SELECT i FROM range(2101) AS t(i) ORDER BY i` using CmdReturn, displayed rows1,001–2,000, then the last101rows with Next disabled. An invalid-column query showed an error and retained the last successful page. The exact app was quit and verified absent. Neutral Plus was separately frozen-smoke tested; its native appearance was not walked again. Earlier native Core results above remain tied to their recorded checkpoint.
