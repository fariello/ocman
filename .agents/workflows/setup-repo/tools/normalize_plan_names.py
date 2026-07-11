#!/usr/bin/env python3
"""
normalize_plan_names.py - check and (on request) normalize plan/prompt filenames to the
canonical convention `YYYYMMDD-HHMM-NN-<slug>.md` (DECISIONS D48/D50).

Deterministic, stdlib-only, standalone (copied into target repos with no import back to the
package). The agent-driven `setup-repo` wizard drives it: `--check` (default) reports which
files do NOT conform and what they would be renamed to; `--apply` performs the renames with
`git mv` (staged, never committed) after the wizard has shown the preview and the user has
agreed.

Convention (unchanged from D48):
  YYYYMMDD-HHMM-NN-<slug>.md
    YYYYMMDD  creation date (UTC)
    HHMM      creation time, 24h (UTC)
    NN        two-digit sequence within that exact YYYYMMDD-HHMM. 00 is reserved (by
              convention, not enforced) for an orchestrator plan; ordinary plans use 01+.
    <slug>    lowercase kebab-case, [a-z0-9-]+, no leading/trailing hyphen.

Timestamp SEMANTICS (D50): the filename timestamp is CREATION/authoring time, stable for the
plan's whole life (not execution, not last-modified). When a legacy file lacks a full
timestamp we derive it from the EARLIEST EVIDENCE of the file's existence:
  min(git-first-commit-time, st_birthtime, st_mtime), in UTC.
A date embedded in the filename ALWAYS wins over the derived value. If the chosen date and
the git-first-commit date differ by more than a day (the tell-tale of an imported/copied
file, whose git-commit records when it entered THIS repo, not when it was authored), the
file is flagged `imported?` and held from auto-rename unless `--assume-dates` is passed.

Scope (D50): by default scans `.agents/plans/` and `.agents/prompts/`. `--area NAME`
(repeatable) replaces that set with exactly the named top-level areas; `--all` scans every
top-level area under `.agents/`. Only `*.md` whose IMMEDIATE parent is a lifecycle dir
(pending/executed/superseded/not-executed/reusable/done) is rename-eligible; files nested
deeper are reported but not renamed unless `--include-nested`. `.agents/workflows/` is never
a rename target.

Usage:
  python3 normalize_plan_names.py --repo .                       # check (text)
  python3 normalize_plan_names.py --repo . --format json          # machine-readable
  python3 normalize_plan_names.py --repo . --all                  # scan every .agents/ area
  python3 normalize_plan_names.py --repo . --area plans           # only plans/
  python3 normalize_plan_names.py --repo . --exclude '*/drafts/*' # extra exclusion
  python3 normalize_plan_names.py --repo . --apply                # staged git mv renames
  python3 normalize_plan_names.py --repo . --apply --assume-dates # also rename imported? files
  python3 normalize_plan_names.py --repo . --apply --rename-non-numeric --include-nested
  python3 normalize_plan_names.py --version

Exit codes: 0 = clean (or --apply succeeded with no held/conflicted items); 1 = items need a
            decision or a conflict occurred; 2 = usage error.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional

AGENTS_DIR = ".agents"
DEFAULT_AREAS = ("plans", "prompts")
LIFECYCLE_SUBDIRS = (
    "pending",
    "executed",
    "superseded",
    "not-executed",
    "reusable",
    "done",
)
# The framework tree is never a rename target regardless of flags.
NEVER_AREA = "workflows"

# Default exclusions: only README.md (the sole framework-owned file that must never be
# renamed). We deliberately do NOT hardcode personal-layout globs like */sources/* (D50).
DEFAULT_EXCLUDES = ("*/README.md", "README.md")

# Canonical form: YYYYMMDD-HHMM-NN-<slug>.md
_NEW_RE = re.compile(
    r"^(?P<date>\d{8})-(?P<time>\d{4})-(?P<nn>\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
# Legacy shapes (ordered; first match wins). Each yields date + optional time/nn + slug.
_LEGACY_RES = (
    # YYYYMMDD-HHMM-<slug>  (time, no NN): 4-digit group
    re.compile(r"^(?P<date>\d{8})-(?P<time>\d{4})-(?P<slug>.+)\.md$"),
    # YYYYMMDD-NN-<slug>    (NN, no time): 2-digit group
    re.compile(r"^(?P<date>\d{8})-(?P<nn>\d{2})-(?P<slug>.+)\.md$"),
    # YYYY-MM-DD-NN-<slug>  (hyphenated date + NN)
    re.compile(
        r"^(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})-(?P<nn>\d{2})-(?P<slug>.+)\.md$"
    ),
    # YYYY-MM-DD-<slug>     (hyphenated date)
    re.compile(r"^(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})-(?P<slug>.+)\.md$"),
    # YYYYMMDD-<slug>       (date only)
    re.compile(r"^(?P<date>\d{8})-(?P<slug>.+)\.md$"),
)
# A parseable YYYYMMDD embedded anywhere in a name (for non-numeric renaming, D50/OQ2).
_EMBEDDED_DATE_RE = re.compile(r"(?<!\d)(\d{8})(?!\d)")


def _framework_version() -> str:
    """Return the framework version from the neighboring VERSION file (three dirs up)."""

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


class Parsed(NamedTuple):
    date: Optional[str]  # compact YYYYMMDD, or None if the name has no leading date
    time: Optional[str]  # HHMM if present in the name, else None
    nn: Optional[str]  # NN if present in the name, else None
    slug: str
    conformant: bool


def normalize_slug(raw: str) -> str:
    """Lowercase kebab-case a slug: [a-z0-9] runs joined by single hyphens; empty -> 'untitled'."""

    s = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return s or "untitled"


def parse_name(filename: str) -> Optional[Parsed]:
    """Parse a plan filename in the canonical or a recognized legacy shape.

    Returns a Parsed (with a compact YYYYMMDD `date`, or None if the name does not start with
    a date), or None if the name matches no known shape (e.g. non-numeric).
    """

    m = _NEW_RE.match(filename)
    if m:
        return Parsed(
            m.group("date"), m.group("time"), m.group("nn"), m.group("slug"), True
        )
    for rx in _LEGACY_RES:
        m = rx.match(filename)
        if not m:
            continue
        gd = m.groupdict()
        if "date" in gd and gd.get("date"):
            date = gd["date"]
        else:
            # Hyphenated YYYY-MM-DD -> compact YYYYMMDD (N-1: no hyphens survive into date).
            date = f"{gd['y']}{gd['mo']}{gd['d']}"
        return Parsed(date, gd.get("time"), gd.get("nn"), gd["slug"], False)
    return None


def is_conformant(filename: str) -> bool:
    """True only for a fully valid canonical name with a clean lowercase-kebab slug."""

    return _NEW_RE.match(filename) is not None


# --------------------------------------------------------------------------------------
# Time resolution: creation proxy = earliest evidence (D50).
# --------------------------------------------------------------------------------------


def _utc_env() -> dict:
    env = dict(os.environ)
    env["TZ"] = "UTC"
    return env


def git_first_commit_stamp(repo_root: Path, rel_path: str) -> Optional[tuple]:
    """Return (date, time) of the file's first commit (author time, UTC), or None.

    Uses `--follow` so a file renamed by earlier migrations traces to its original add, and
    takes the OLDEST such author time. None on any failure (non-git, untracked, git missing).
    """

    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "log",
                "--follow",
                "--diff-filter=A",
                "--date=format-local:%Y%m%d %H%M",
                "--format=%ad",
                "--",
                rel_path,
            ],
            capture_output=True,
            text=True,
            env=_utc_env(),
        )
    except (OSError, ValueError):
        return None
    if proc.returncode != 0:
        return None
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    oldest = lines[-1]  # git log is newest-first
    parts = oldest.split()
    if len(parts) != 2:
        return None
    return (parts[0], parts[1])


def fs_stamp(path: Path) -> Optional[tuple]:
    """Return the earliest of the file's birthtime/mtime as a UTC (date, time), or None.

    st_birthtime is used when the platform/FS exposes it (macOS/Windows-origin); absent on
    Linux ext4. st_ctime is NOT used as a value (Linux inode-change time is not creation).
    """

    try:
        st = path.stat()
    except OSError:
        return None
    epochs = []
    bt = getattr(st, "st_birthtime", None)
    if bt:
        epochs.append(bt)
    if st.st_mtime:
        epochs.append(st.st_mtime)
    if not epochs:
        return None
    dt = datetime.datetime.fromtimestamp(min(epochs), datetime.timezone.utc)
    return (dt.strftime("%Y%m%d"), dt.strftime("%H%M"))


def _min_stamp(*stamps) -> Optional[tuple]:
    """Return the earliest (date, time) among the non-None stamps, or None."""

    present = [s for s in stamps if s is not None]
    if not present:
        return None
    return min(present)  # tuple compare on (date, time) strings, both zero-padded


def _days_apart(a: tuple, b: tuple) -> int:
    """Absolute difference in days between two (date, time) stamps (date part only)."""

    def to_date(s):
        return datetime.date(int(s[0][:4]), int(s[0][4:6]), int(s[0][6:8]))

    return abs((to_date(a) - to_date(b)).days)


class Resolution(NamedTuple):
    date: str
    time: str
    imported: bool  # chosen date disagrees with git first-commit by > 1 day


def resolve_creation(
    repo_root: Path, rel_path: str, parsed: Optional[Parsed]
) -> Resolution:
    """Resolve the canonical (date, time) for a file, per D50 earliest-evidence rules.

    - A filename-embedded/leading date wins for the DATE; time comes from the earliest
      evidence (or the name's own time, or 0000).
    - Else the whole (date, time) is the earliest of git-first-commit / birthtime / mtime.
    - `imported` is set when the chosen date disagrees with git-first-commit by > 1 day.
    """

    path = repo_root / rel_path
    git = git_first_commit_stamp(repo_root, rel_path)
    fs = fs_stamp(path)
    earliest = _min_stamp(git, fs)  # evidence signals only (name-date is separate)

    name_date = parsed.date if parsed else None
    name_time = parsed.time if parsed else None

    if name_date:
        date = name_date
        if name_time:
            time = name_time
        elif earliest:
            time = earliest[1]
        else:
            time = "0000"
        chosen = (date, time)
    elif earliest:
        chosen = earliest
        date, time = earliest
    else:
        # Effectively unreachable: stat() succeeds for an existing file.
        date, time = (name_date or "00000000"), "0000"
        chosen = (date, time)

    imported = bool(git) and _days_apart(chosen, git) > 1
    return Resolution(date, time, imported)


# --------------------------------------------------------------------------------------
# Scan + rename plan.
# --------------------------------------------------------------------------------------


class Item(NamedTuple):
    old: str  # repo-relative posix path
    new: str  # repo-relative posix path (== old when not renamed)
    status: str  # conformant | to-rename | imported | excluded | nested | non-numeric | conflict
    detail: str = ""


# Back-compat alias: earlier tests use Rename(old, new, reason) with .reason.
class Rename(NamedTuple):
    old: str
    new: str
    reason: str


def _is_excluded(rel: str, excludes) -> bool:
    return any(fnmatch.fnmatch(rel, pat) for pat in excludes)


def _resolve_areas(all_areas: bool, areas) -> Optional[list]:
    """Return the list of area names to scan; None means 'every top-level area under .agents/'."""

    if all_areas:
        return None
    if areas:
        return list(areas)
    return list(DEFAULT_AREAS)


def scan(
    repo_root,
    subdirs=None,  # back-compat: ignored in favor of area/lifecycle logic
    *,
    areas=None,
    all_areas: bool = False,
    excludes=None,
    include_default_excludes: bool = True,
    include_nested: bool = False,
    rename_non_numeric: bool = False,
    assume_dates: bool = False,
):
    """Scan the repo and return a list of Rename items (old, new, reason/status).

    reason/status values: conformant (omitted from result), to-rename, imported, excluded,
    nested, non-numeric, conflict. A `Rename` with old == new is a non-rename report entry.
    Default behavior (no kwargs) matches the historical `scan(repo_root)`: scan plans+prompts,
    README-only excludes, no nesting, no non-numeric renaming.
    """

    repo_root = Path(repo_root)
    base = list(DEFAULT_EXCLUDES) if include_default_excludes else []
    excludes = base + list(excludes or [])
    area_list = _resolve_areas(all_areas, areas)
    agents = repo_root / AGENTS_DIR

    # Determine which top-level area dirs to walk.
    if area_list is None:
        area_dirs = [
            d for d in sorted(agents.glob("*")) if d.is_dir() and d.name != NEVER_AREA
        ]
    else:
        area_dirs = [
            agents / a for a in area_list if (agents / a).is_dir() and a != NEVER_AREA
        ]

    # First pass: gather all *.md under a lifecycle dir (any depth), classify, and seed
    # the NN-taken map from already-conformant files.
    taken: dict = {}
    eligible = []  # (rel, parsed_or_None, is_immediate_child)
    for area_dir in area_dirs:
        for md in sorted(area_dir.rglob("*.md")):
            rel = md.relative_to(repo_root).as_posix()
            # Must live under a recognized lifecycle dir somewhere in its path.
            parts = md.relative_to(area_dir).parts
            # parts[0] is the lifecycle subdir; the file is an immediate child iff len==2.
            if not parts or parts[0] not in LIFECYCLE_SUBDIRS:
                continue
            immediate = len(parts) == 2
            name = md.name
            if is_conformant(name):
                p = parse_name(name)
                if p is not None and p.nn is not None:
                    taken.setdefault((p.date, p.time), set()).add(int(p.nn))
                continue
            eligible.append((rel, parse_name(name), immediate))

    results = []
    for rel, parsed, immediate in eligible:
        if _is_excluded(rel, excludes):
            results.append(Rename(rel, rel, "excluded"))
            continue
        if not immediate and not include_nested:
            results.append(Rename(rel, rel, "nested"))
            continue
        if parsed is None:
            # Non-numeric (no leading date). Off by default.
            if not rename_non_numeric:
                results.append(Rename(rel, rel, "non-numeric"))
                continue
            parsed = _synthesize_parsed_for_nonnumeric(rel)

        res = resolve_creation(repo_root, rel, parsed)
        if res.imported and not assume_dates:
            results.append(Rename(rel, rel, "imported"))
            continue

        subdir = Path(rel).parent.as_posix()
        slug = normalize_slug(parsed.slug)
        date, time = res.date, res.time
        # Preserve a real NN already in the name; else assign next free (never 00).
        used = taken.setdefault((date, time), set())
        if parsed.nn is not None and int(parsed.nn) not in used and int(parsed.nn) != 0:
            nn = int(parsed.nn)
        else:
            nn = 1
            while nn in used:
                nn += 1
        candidate_rel = f"{subdir}/{date}-{time}-{nn:02d}-{slug}.md"
        # Target-collision guard.
        guard = 0
        while (
            (repo_root / candidate_rel).exists()
            and candidate_rel != rel
            and guard < 100
        ):
            nn += 1
            while nn in used:
                nn += 1
            candidate_rel = f"{subdir}/{date}-{time}-{nn:02d}-{slug}.md"
            guard += 1
        if (repo_root / candidate_rel).exists() and candidate_rel != rel:
            results.append(Rename(rel, rel, "conflict"))
            continue
        used.add(nn)
        results.append(Rename(rel, candidate_rel, "to-rename"))

    return results


def _synthesize_parsed_for_nonnumeric(rel: str) -> Parsed:
    """Build a Parsed for a non-numeric file: use an embedded YYYYMMDD if present (D50/OQ2)."""

    stem = Path(rel).name[: -len(".md")] if rel.endswith(".md") else Path(rel).name
    m = _EMBEDDED_DATE_RE.search(stem)
    if m:
        date = m.group(1)
        # Drop the consumed date from the slug source.
        slug_src = stem[: m.start()] + stem[m.end() :]
        return Parsed(date, None, None, slug_src, False)
    return Parsed(None, None, None, stem, False)


def _git_tracked(repo_root: Path, rel: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", rel],
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError):
        return False
    return proc.returncode == 0


def apply(renames, repo_root, use_git: bool = True) -> list:
    """Perform the to-rename items via `git mv` (staged, not committed); never clobber.

    Non-rename statuses (excluded/nested/non-numeric/imported/conflict, and any old==new) are
    reported and skipped. Returns human-readable action strings.
    """

    repo_root = Path(repo_root)
    actions = []
    for r in renames:
        reason = getattr(r, "reason", None) or getattr(r, "status", "")
        if r.old == r.new or reason != "to-rename":
            if reason and reason != "conformant":
                actions.append(f"{reason.upper()} (skipped): {r.old}")
            continue
        dest = repo_root / r.new
        if dest.exists():
            actions.append(f"CONFLICT (target exists, skipped): {r.old} -> {r.new}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if use_git and _git_tracked(repo_root, r.old):
            proc = subprocess.run(
                ["git", "-C", str(repo_root), "mv", "--", r.old, r.new],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                (repo_root / r.old).rename(dest)
                subprocess.run(
                    ["git", "-C", str(repo_root), "add", "--", r.new, r.old],
                    capture_output=True,
                    text=True,
                )
        else:
            (repo_root / r.old).rename(dest)
        actions.append(f"renamed: {r.old} -> {r.new}")
    return actions


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Check/normalize plan filenames to YYYYMMDD-HHMM-NN-<slug>.md."
    )
    ap.add_argument(
        "--version", action="store_true", help="Print framework version and exit."
    )
    ap.add_argument(
        "--repo", default=".", help="Repository root (default: current dir)."
    )
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument(
        "--area",
        action="append",
        default=None,
        help="Top-level .agents/ area to scan (repeatable); replaces the default "
        "plans+prompts set. E.g. --area plans --area prompts.",
    )
    ap.add_argument(
        "--all",
        dest="all_areas",
        action="store_true",
        help="Scan every top-level area under .agents/ (never .agents/workflows/).",
    )
    ap.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="fnmatch glob (repo-relative path) to exclude (repeatable).",
    )
    ap.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Drop the built-in README.md default exclude.",
    )
    ap.add_argument(
        "--include-nested",
        action="store_true",
        help="Also rename eligible *.md nested below a lifecycle dir.",
    )
    ap.add_argument(
        "--rename-non-numeric",
        action="store_true",
        help="Also rename files that do not start with a date (opt-in).",
    )
    ap.add_argument(
        "--assume-dates",
        action="store_true",
        help="Accept derived dates for files flagged 'imported?' and rename them.",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Perform the staged git-mv renames (default is check-only).",
    )
    args = ap.parse_args(argv)

    if args.version:
        print(_framework_version())
        return 0

    repo_root = Path(args.repo).expanduser().resolve()
    items = scan(
        repo_root,
        areas=args.area,
        all_areas=args.all_areas,
        excludes=args.exclude,
        include_default_excludes=not args.no_default_excludes,
        include_nested=args.include_nested,
        rename_non_numeric=args.rename_non_numeric,
        assume_dates=args.assume_dates,
    )

    to_rename = [r for r in items if r.reason == "to-rename"]
    needs_decision = [
        r for r in items if r.reason in ("imported", "non-numeric", "conflict")
    ]

    if args.apply:
        actions = apply(items, repo_root)
        skipped = [a for a in actions if "(skipped)" in a]
        if args.format == "json":
            print(json.dumps({"actions": actions}, indent=2))
        else:
            for a in actions:
                print(a)
            print(
                f"\n{len(actions) - len(skipped)} renamed (staged), {len(skipped)} skipped."
            )
        return 1 if needs_decision else 0

    # Check mode.
    if args.format == "json":
        print(
            json.dumps(
                {
                    "items": [
                        {"old": r.old, "new": r.new, "status": r.reason}
                        for r in items
                        if r.reason != "conformant"
                    ]
                },
                indent=2,
            )
        )
    else:
        reportable = [r for r in items if r.reason != "conformant"]
        if not reportable:
            print(
                "All scanned plan/prompt filenames conform to YYYYMMDD-HHMM-NN-<slug>.md."
            )
        else:
            print("Filenames that are not canonical (old -> proposed new / status):")
            for r in reportable:
                if r.reason == "to-rename":
                    print(f"  {r.old}  ->  {r.new}")
                elif r.reason == "imported":
                    print(
                        f"  {r.old}  [imported? git-vs-chosen date differ; needs --assume-dates]"
                    )
                elif r.reason == "non-numeric":
                    print(f"  {r.old}  [non-numeric; needs --rename-non-numeric]")
                elif r.reason == "nested":
                    print(f"  {r.old}  [nested; needs --include-nested]")
                elif r.reason == "excluded":
                    print(f"  {r.old}  [excluded]")
                elif r.reason == "conflict":
                    print(f"  {r.old}  [conflict: cannot assign a free name]")
            print(
                f"\n{len(to_rename)} ready to rename, {len(needs_decision)} need a decision."
            )
    return 1 if (to_rename or needs_decision) else 0


if __name__ == "__main__":
    raise SystemExit(main())
