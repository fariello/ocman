#!/usr/bin/env python3
"""One-shot migration: normalize legacy ocman recovery filenames to the canonical scheme.

Newer ocman writes recovery artifacts as ``YYYYMMDD-HHMM-<session_id>.<kind>.md`` (local time),
where ``<kind>`` is one of transcript/restart/prompt/compacted. Older versions used
``opencode-YYYYMMDD-HHMMSS-<sid>.<kind>.md`` (UTC seconds) and a date-only in-project copy
``YYYYMMDD-<sid>.<kind>.md``. This script renames files already on disk to the canonical form.

Safety:
  * Operates on the given directory ONLY, top-level (no recursion, no implicit scanning).
  * Skips symlinks (never follows or renames through them).
  * Never writes outside the target directory.
  * Skips files already canonical; refuses to overwrite an existing target unless --force.
  * Uses os.rename within the directory; if it fails, the source is left untouched.

Usage:
    python scripts/migrate_recovery_names.py <dir> [--yes] [--force] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Make the sibling ocman module importable when run from a checkout.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ocman import (  # noqa: E402
    RECOVERY_KINDS,
    canonical_recovery_name,
    parse_recovery_name,
)


def plan_migration(directory: Path) -> list[tuple[Path, Path]]:
    """Return the list of (source, target) renames for recovery files in ``directory``.

    Top-level only; symlinks skipped; already-canonical files omitted. Timestamp comes from the
    parsed filename, else the file's mtime (local time).
    """
    directory = directory.resolve()
    renames: list[tuple[Path, Path]] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_symlink() or not entry.is_file():
            continue
        session_id, dt, kind = parse_recovery_name(entry)
        if not kind or kind not in RECOVERY_KINDS:
            continue
        if dt is None:
            try:
                dt = datetime.fromtimestamp(entry.stat().st_mtime)
            except OSError:
                continue
        if not session_id:
            continue
        target_name = canonical_recovery_name(session_id, dt, kind)
        if target_name == entry.name:
            continue  # already canonical
        renames.append((entry, directory / target_name))
    return renames


def migrate_dir(
    directory: Path,
    *,
    apply: bool,
    force: bool,
    log=print,
) -> dict[str, int]:
    """Execute (or preview) the migration. Returns a summary of counts.

    ``apply=False`` is a dry run (no filesystem changes).
    """
    directory = directory.resolve()
    summary = {"renamed": 0, "skipped_collision": 0, "errors": 0, "planned": 0}
    renames = plan_migration(directory)
    summary["planned"] = len(renames)
    for src, dst in renames:
        if dst.exists() and not force:
            log(f"  SKIP (target exists): {src.name} -> {dst.name}")
            summary["skipped_collision"] += 1
            continue
        # Containment guard: dst must stay inside the directory.
        if dst.resolve().parent != directory:
            log(f"  SKIP (outside dir): {src.name} -> {dst}")
            summary["errors"] += 1
            continue
        log(f"  {'RENAME' if apply else 'WOULD RENAME'}: {src.name} -> {dst.name}")
        if apply:
            try:
                os.rename(src, dst)  # atomic within one filesystem; never unlinks source on failure
                summary["renamed"] += 1
            except OSError as e:
                log(f"  ERROR renaming {src.name}: {e}")
                summary["errors"] += 1
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_recovery_names.py",
        description="Normalize legacy ocman recovery filenames to YYYYMMDD-HHMM-<sid>.<kind>.md.",
    )
    parser.add_argument("directory", type=Path, help="Directory to normalize (top-level only).")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target names.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing files.")
    args = parser.parse_args(argv)

    directory = args.directory
    if not directory.is_dir():
        print(f"Error: not a directory: {directory}", file=sys.stderr)
        return 2

    renames = plan_migration(directory)
    if not renames:
        print("Nothing to do: no legacy recovery filenames found (or all are already canonical).")
        return 0

    print(f"Planned renames in {directory.resolve()} (top-level only):")
    for src, dst in renames:
        print(f"  {src.name} -> {dst.name}")

    if args.dry_run:
        print(f"\nDry run: {len(renames)} file(s) would be renamed. No changes made.")
        return 0

    if not args.yes:
        answer = input(f"\nRename {len(renames)} file(s)? [Y/n]: ").strip().lower()
        if answer in {"n", "no"}:
            print("Cancelled.")
            return 1

    summary = migrate_dir(directory, apply=True, force=args.force)
    print(
        f"\nDone: {summary['renamed']} renamed, "
        f"{summary['skipped_collision']} skipped (collision), "
        f"{summary['errors']} error(s)."
    )
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
