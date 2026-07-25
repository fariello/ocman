# Evidence inspected - assess documentation (20260725-104354)

Read-only. No project files were modified. Reproducible inputs below.

## Docs inspected
- README.md (654 lines) - full read of the Command Reference, Configuration, Getting Started,
  Known Limitations sections.
- CHANGELOG.md - [Unreleased] and [1.3.0] sections.
- ARCHITECTURE.md - scanned for user-facing version strings (none that drift).
- pyproject.toml - version (7), requires-python (11), dependencies (15-20), scripts (29-30).

## Code cross-checked (ocman/cli.py unless noted)
- Version: pyproject.toml:7 (1.3.0) == ocman/cli.py:208 (__version__).
- CLI surface: build_parser / new_sub / add_argument enumerated across ocman/cli.py:6199-6579.
  Key rows verified: kill (6456-6465), running/lr (6525-6535), reconnect (6449-6453),
  rename (6468-6479), export (6482-6487), spend (6497-6504), doctor (6537-6548),
  session/project/db/backup/history/config groups (6236-6425).
- kill PID + preview: metavar PID|PATTERN at 6458-6460; PID branch 12446-12453; enriched preview
  block 12500-12514 (Kind/Uptime/Project/Session and conditional Listener/Auth).
- Config: DEFAULT_CONFIG (309-327), DEFAULT_CONFIG_TEMPLATE (226-307), load/merge (331-408),
  OCMAN_CONFIG_PATH constant (224). Verified every README config key/default (README.md:463-513)
  matches DEFAULT_CONFIG 1:1.
- Env vars: NO_COLOR/FORCE_COLOR (139-145, ~5480-5486); OPENCODE_DB / XDG_DATA_HOME /
  OPENCODE_CONFIG_DIR in discover_storage_locations (~13822/13834/13840). Confirmed OCMAN_CONFIG_PATH
  is NOT read from the environment anywhere in ocman/ (grep for environ/getenv).

## Commands run (read-only)
- `ls *.md`; `find . -maxdepth 2 -name '*.md'` (doc inventory)
- `grep -nP 'version|name =|console_scripts|scripts|^\[project' pyproject.toml`
- `grep -nP 'ocman kill|OCMAN_CONFIG_PATH|PID' README.md`
- `grep -rnP 'OCMAN_CONFIG_PATH' ocman/`
- `grep -rnP 'environ.*OCMAN_CONFIG|getenv.*OCMAN_CONFIG' ocman/` (NONE)
- `grep -nP 'ocman spend|### .history|Top-level verbs' README.md`
- Delegated a thorough README-vs-code audit to an explore sub-agent (full CLI enumeration +
  config/env verification); the two highest-severity findings (AD-01, AD-02) were then
  re-verified directly against source by the orchestrator.

## Sampling / truncation notes
- ocman/cli.py is ~17k lines; inspection targeted the parser-construction region (6199-6579), the
  kill implementation (12446-12514), and the config/env code paths rather than a full line read.
- README examples were spot-checked against the parser (db clean duration forms, recovery flags,
  compact specs, disk/info aliases); no stale flags found in examples.
