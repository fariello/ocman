#!/usr/bin/env bash
# Install ocman as an editable install that actually tracks the working tree.
#
# hatchling's force-include (needed so ocman.py ships in real wheels) also copies
# ocman.py into site-packages during `pip install -e .`. That copy shadows the
# editable .pth redirect and goes stale whenever ocman.py changes, so the
# installed `ocman` command silently runs old code. This script installs
# editable, then removes the shadow copy so the .pth serves the repo.
#
# Usage: scripts/dev-editable-install.sh [python]
set -euo pipefail

PY="${1:-python3}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT"
"$PY" -m pip install -e .

# Remove the shadow copy (and its bytecode) from every site-packages dir.
"$PY" - <<'PYEOF'
import site, sysconfig, pathlib, itertools
dirs = set()
for d in (site.getsitepackages() if hasattr(site, "getsitepackages") else []):
    dirs.add(d)
dirs.add(sysconfig.get_paths()["purelib"])
for d in dirs:
    for p in (pathlib.Path(d) / "ocman.py",):
        if p.exists():
            print(f"removing shadow copy: {p}")
            p.unlink()
    pc = pathlib.Path(d) / "__pycache__"
    if pc.is_dir():
        for f in pc.glob("ocman.*.pyc"):
            f.unlink()
PYEOF

echo "Verifying import resolves to the working tree..."
"$PY" -c "import ocman; print('ocman ->', ocman.__file__)"
