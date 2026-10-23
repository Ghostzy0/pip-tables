# Projects, upgrades and portability

Format2 is the first supported Tables project format. A project folder contains data.duckdb imported snapshots and project.json query history/draft. Files are plaintext; source paths are recorded. There is no automatic cloud backup.

Before an upgrade, quit the app and copy the WHOLE folder to another location. Open the copy explicitly in the new app. Core and Plus share format 2 and never automatically migrate or replace a project. Each named package has its own application identity; Pip Core/Plus appearance preferences are separate. Do not open the same project concurrently in two running editions.

Unreleased format 1 development fixtures are rejected unchanged. They need their original development checkout; no destructive migration is supplied. A corrupt or unsupported folder is rejected; preserve it and report a synthetic reproduction.

For interchange choose Parquet when typed values matter. CSV/XLSX safe formula handling and exact-number text encodings change some text values; JSON dates/decimals/binary use documented encodings. These are result exports, not whole-project backups. Export never replaces an existing file.

To remove your data, quit Tables and remove only the project folder you selected. Keep backups according to your needs. This source does not include an uninstaller that scans or removes personal folders.
