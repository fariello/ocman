#!/usr/bin/env bash
# Install ocman as an editable install that actually tracks the working tree.
#
# Packaging ocman as a package directory (ocman/) resolves the editable shadow
# copy problem naturally. This script cleans up any leftover stale shadow copies 
# of the old ocman.py in site-packages, runs the editable install, and verifies.
#
# Usage: scripts/dev-editable-install.sh [python]
set -euo pipefail

PY="${1:-python3}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT"

# Clean up any leftover stale shadow copy from previous packaging layouts
"$PY" - <<'PYEOF'
import site, sysconfig, pathlib
dirs = set()
for d in (site.getsitepackages() if hasattr(site, "getsitepackages") else []):
    dirs.add(d)
dirs.add(sysconfig.get_paths()["purelib"])
for d in dirs:
    p = pathlib.Path(d) / "ocman.py"
    if p.exists():
        print(f"Removing leftover shadow copy: {p}")
        p.unlink()
    pc = pathlib.Path(d) / "__pycache__"
    if pc.is_dir():
        for f in pc.glob("ocman.*.pyc"):
            print(f"Removing leftover bytecode: {f}")
            f.unlink()
PYEOF

"$PY" -m pip install -e .

echo "Verifying import resolves to the working tree..."
"$PY" -c "import ocman; print('ocman ->', ocman.__file__)"
