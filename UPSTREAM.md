# Foundation and provenance

23 October 2026. All four configurations are original implementations. No Julius or Duckling code, trademarks, UI assets, reference screenshots or proprietary motion code are included.

## References examined

- [Julius service description](https://julius.ai/faq/service-description) and [start guide](https://julius.ai/faq/chat-start-guide): upload, analyse, chart and export are documented workflows. A bounded free-account workflow was observed after explicit owner consent to the terms. Pasted synthetic CSV produced 12 rows, 11 non-null amounts, exact total 1384.25 and regional totals North 555.75 / South 419.75 / West 408.75, plus a chart and CSV preview. File upload was blocked by a browser extension file-URL permission, which was left unchanged. Actual downloaded output was not verified. Broader parity remains unverified. The app is independently implemented; no affiliation claimed.
- [Duckling MIT source](https://github.com/l1xnan/duckling/tree/02f9696bd57e554af1e370440928a4f1c79f420e), release v0.59.3 inspected by research: SQL/grid/history/file-import reference. Its credential/remote-connector/updater footprint was unnecessary for the local accountless product, so no code imported and no claim that its vendor binary was reproduced.
- [DuckDB v1.4.3](https://github.com/duckdb/duckdb/releases/tag/v1.4.3), tag commit `d1dc88f950d456d72493df452dabdcd13aa413dd`. Embedded computation dependency, MIT; version pinned deliberately rather than described as latest. Python wheel from PyPI, native arm64 in the tested macOS build.
- [DuckDB security guidance](https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview): user SQL is untrusted. This application adds read-only connections, one-statement parsing, disabled external access/extensions, memory limits, time limits and bounded previews. This is not a claim of a process security sandbox against malicious engine exploits.
- [Qt for Python licensing](https://doc.qt.io/qtforpython-6/licenses.html): PySide6 Essentials 6.10.2 / Shiboken6 6.10.2; LGPLv3 dynamic libraries, not statically linked. Qt's system platform integration is retained.
- [openpyxl](https://pypi.org/project/openpyxl/3.1.5/) 3.1.5 and et-xmlfile 2.0.0: MIT. Selected-sheet XLSX import and export, no external Excel extension or internet download.

## Code, assets and data

Application source and original character rendering: MIT. Uses system typography; no proprietary font copied. Example records are synthetic and explicitly labelled. No models, AI providers, analytics, network client, updater or hosted runtime in core. Both editions use the identical data engine and workflow; baseline uses native system styling, Pip adds original guide-informed styling. Dependency licence copies and build inventory accompany each package.

Discovery social-post statistics in the assignment are unverified scouting context and are not treated as demand evidence or product acceptance. Public docs avoid repeating them as verified counts.
