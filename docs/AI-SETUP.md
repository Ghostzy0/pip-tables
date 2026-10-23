# Ask an AI to set up Tables

Copy this into an assistant that has local file and terminal access:

> Set up Ghostzy0/pip-tables on my Apple Silicon Mac using its README and pinned requirements-lock.txt in a fresh virtual environment. Run tests and the synthetic smoke check, then launch the Pip edition; keep my files untouched and report any unsupported platform or failed check.

Explicit commands, from a clone on macOS 13+ arm64 with Python 3.13 installed:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m pip_tables --smoke /tmp/tables-smoke.json
.venv/bin/python -m pip_tables --edition pip
```

For the system-styled edition change the final edition argument to `baseline`. Add `--enhanced` for Plus import inspection and result pages. No tokens, account linking, paid endpoint or administrator command is needed. Installation downloads pinned Python packages from PyPI. Do not execute remote shell scripts or upload the owner's datasets. For packaging, run `scripts/build.py baseline`, `pip`, `baseline-plus` or `pip-plus`; verify the actual bundle with its smoke command. Preserve project folders on every upgrade. Source support is currently macOS arm64; other systems are not validated by this recipe.
