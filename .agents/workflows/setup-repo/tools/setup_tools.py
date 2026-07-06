#!/usr/bin/env python3
"""
setup_tools.py - detect and (on request) install the developer tools used by the
setup-repo wizard's best-practice checks.

This is the deterministic, mechanical layer that the agent-driven `setup-repo` wizard
orchestrates. By default it only DETECTS and reports status + how to install each tool;
it installs a tool only when explicitly asked (`--install NAME`), and even then it runs
the platform's own package manager (it does not download-and-pipe-to-shell). The wizard
asks the user before invoking any install.

Tools it knows about:
  gitleaks        - secret scanner (binary; used by CI and pre-commit)
  pre-commit      - multi-hook git pre-commit framework (Python)
  detect-secrets  - secret scanner / pre-commit baseline (Python)

Usage:
  python3 setup_tools.py                 # detect + report all tools (read-only)
  python3 setup_tools.py --format json   # machine-readable status
  python3 setup_tools.py --install gitleaks         # attempt install (asks nothing;
                                                      the WIZARD is responsible for
                                                      having confirmed with the user)
  python3 setup_tools.py --install gitleaks,pre-commit

Exit codes: 0 = ok (detect, or all requested installs succeeded);
            1 = one or more requested installs failed;
            2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _framework_version() -> str:
    """Return the agent-workflows framework version this tool ships with.

    The VERSION file lives at the framework root (.agents/workflows/VERSION); this script
    is at .agents/workflows/setup-repo/tools/setup_tools.py, so it is three directories up.
    Returns "unknown" if the file is absent (e.g. run standalone outside the framework).
    """

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def which(name: str) -> str | None:
    return shutil.which(name)


def detect_package_managers() -> list[str]:
    """Return available package managers, best-first for the current platform."""

    candidates = ["brew", "apt-get", "dnf", "pacman", "zypper", "pipx", "pip3", "pip", "go"]
    return [c for c in candidates if which(c)]


# Per-tool: how to check version, and ordered (manager -> install argv) options.
TOOLS: dict[str, dict] = {
    "gitleaks": {
        "purpose": "Secret scanner (binary). Used by the secret-scan CI workflow and the local pre-commit hook.",
        "version_cmd": ["gitleaks", "version"],
        "installers": [
            ("brew", ["brew", "install", "gitleaks"]),
            ("go", ["go", "install", "github.com/gitleaks/gitleaks/v8@latest"]),
        ],
        "manual": "Download a release binary from https://github.com/gitleaks/gitleaks/releases and put it on PATH.",
    },
    "pre-commit": {
        "purpose": "Multi-hook git pre-commit framework (runs secret scan, formatting, large-file checks, etc. on commit).",
        "version_cmd": ["pre-commit", "--version"],
        "installers": [
            ("pipx", ["pipx", "install", "pre-commit"]),
            ("brew", ["brew", "install", "pre-commit"]),
            ("pip3", ["pip3", "install", "--user", "pre-commit"]),
            ("pip", ["pip", "install", "--user", "pre-commit"]),
        ],
        "manual": "https://pre-commit.com/#install",
    },
    "detect-secrets": {
        "purpose": "Secret scanner with a committed baseline; handy as a local/pre-commit helper.",
        "version_cmd": ["detect-secrets", "--version"],
        "installers": [
            ("pipx", ["pipx", "install", "detect-secrets"]),
            ("pip3", ["pip3", "install", "--user", "detect-secrets"]),
            ("pip", ["pip", "install", "--user", "detect-secrets"]),
        ],
        "manual": "https://github.com/Yelp/detect-secrets",
    },
}


def tool_version(name: str) -> str | None:
    spec = TOOLS[name]
    if not which(spec["version_cmd"][0]):
        return None
    try:
        p = subprocess.run(spec["version_cmd"], capture_output=True, text=True, timeout=15)
        return (p.stdout or p.stderr).strip().splitlines()[0] if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def install_hint(name: str, managers: list[str]) -> str:
    """The recommended install command for the current platform, or manual guidance."""

    for mgr, argv in TOOLS[name]["installers"]:
        if mgr in managers:
            return " ".join(argv)
    return TOOLS[name]["manual"]


def detect(managers: list[str]) -> dict[str, dict]:
    status = {}
    for name in TOOLS:
        ver = tool_version(name)
        status[name] = {
            "installed": ver is not None,
            "version": ver,
            "purpose": TOOLS[name]["purpose"],
            "install_hint": None if ver else install_hint(name, managers),
        }
    return status


def do_install(name: str, managers: list[str]) -> tuple[bool, str]:
    """Attempt to install one tool using the first available known manager.

    The wizard is responsible for having confirmed with the user first.
    """

    if name not in TOOLS:
        return False, f"unknown tool: {name}"
    if tool_version(name):
        return True, f"{name} already installed"

    for mgr, argv in TOOLS[name]["installers"]:
        if mgr not in managers:
            continue
        # apt-get needs the update/sudo dance; only attempt if it is the chosen mgr.
        cmd = argv
        try:
            p = subprocess.run(cmd, text=True)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, f"{name}: '{' '.join(cmd)}' failed to run ({exc})"
        if p.returncode == 0 and tool_version(name):
            return True, f"{name}: installed via {mgr}"
        # try next manager
    return False, (f"{name}: no known installer succeeded. Install manually: "
                   f"{TOOLS[name]['manual']}")


def report_text(status: dict[str, dict], managers: list[str]) -> None:
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Package managers available: {', '.join(managers) or 'none detected'}")
    print()
    print("Developer tools for repo best-practice checks:")
    for name, s in status.items():
        mark = "OK " if s["installed"] else "MISSING"
        print(f"  [{mark}] {name}: {s['version'] or s['purpose']}")
        if not s["installed"]:
            print(f"           install: {s['install_hint']}")
    missing = [n for n, s in status.items() if not s["installed"]]
    if missing:
        print()
        print("To let the setup-repo wizard install a tool for you (after confirming),")
        print(f"it will run: python3 setup_tools.py --install {','.join(missing)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect/install developer tools for repo setup.")
    ap.add_argument("--version", action="store_true",
                    help="Print the agent-workflows framework version and exit.")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--install", default="", help="Comma-separated tool names to install.")
    args = ap.parse_args()

    if args.version:
        print(_framework_version())
        return 0

    managers = detect_package_managers()

    if args.install:
        names = [n.strip() for n in args.install.split(",") if n.strip()]
        unknown = [n for n in names if n not in TOOLS]
        if unknown:
            print(f"Unknown tool(s): {', '.join(unknown)}. Known: {', '.join(TOOLS)}", file=sys.stderr)
            return 2
        ok = True
        results = []
        for n in names:
            success, msg = do_install(n, managers)
            ok = ok and success
            results.append({"tool": n, "ok": success, "message": msg})
            print(("OK:   " if success else "FAIL: ") + msg, file=sys.stderr)
        if args.format == "json":
            json.dump({"installed": results}, sys.stdout, indent=2)
            sys.stdout.write("\n")
        return 0 if ok else 1

    status = detect(managers)
    if args.format == "json":
        json.dump({"platform": f"{platform.system()} {platform.machine()}",
                   "package_managers": managers, "tools": status}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        report_text(status, managers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
