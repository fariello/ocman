#!/usr/bin/env python3
"""
run_checks.py - discover and run a repository's OWN checks, and capture real evidence.

Turns "the agent says the tests pass" into "here is machine-checkable evidence": it
DISCOVERS the repo's declared test/lint/build/type-check commands (from package.json
scripts, Makefile, pyproject/tox, justfile, and CI workflow files), runs the ones you
approve, and records the actual command, exit code, duration, key metrics, and a
truncated log excerpt into a structured result. It is dependency-free (Python stdlib
only), matching scan_secrets.py.

SAFETY (running repo commands is the core hazard):
  - Discovery only PROPOSES commands; nothing runs without approval. Default is
    confirm-before-each-check; --yes runs the approved/allowlisted set non-interactively.
  - Only commands classified as test / lint / build / type-check are eligible to run.
    A hard DENYLIST blocks anything that looks like network / deploy / publish / install /
    push / release, even if it was discovered - these are never run.
  - Ambiguous / unclassified commands are NEVER auto-run; they require explicit approval
    (interactive y) and are skipped under --yes.
  - Each command is time-bounded (--timeout) and run in the repo root. Output is captured,
    not acted upon. No network calls are made by this tool itself.

HONESTY: the result records what ran, what was SKIPPED and why (denied, unclassified,
declined, timed out, discovery-only), and never marks a check "passed" that it did not
actually run to a zero exit. A partial run must never read as a full green - the summary
reports ran / passed / failed / skipped separately.

Usage:
    python3 run_checks.py [--repo PATH] [--format json|csv|text] [--out FILE]
                          [--list] [--yes] [--timeout SECONDS]
                          [--only CATEGORY[,CATEGORY...]] [--add "CMD"] [--version]

Exit codes: 0 = run completed AND every check that ran passed (or nothing was run);
            1 = at least one check that ran FAILED (non-zero exit or timeout);
            2 = usage/environment error.
(The exit code reflects only checks actually run; skipped checks never make it "pass".)
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path


# ---- Classification --------------------------------------------------------

# Categories eligible to run. A discovered command is classified by matching keywords in
# its name (the script/target name) and, secondarily, its command text.
ALLOWED_CATEGORIES = ("test", "lint", "build", "typecheck")

# Keyword -> category. Checked against the task NAME first (most reliable), then the text.
CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    (r"\btype[-_ ]?check\b|\btypecheck\b|\bmypy\b|\bpyright\b|\btsc\b|\bflow\b", "typecheck"),
    (r"\btest\b|\btests\b|\bpytest\b|\bunittest\b|\bjest\b|\bvitest\b|\bmocha\b|\bgo test\b|\bcargo test\b|\bspec\b", "test"),
    (r"\blint\b|\bflake8\b|\bruff\b|\beslint\b|\bpylint\b|\bclippy\b|\bvet\b|\bfmt[-_ ]?check\b|\bcheck[-_ ]?format\b|\bstyle\b", "lint"),
    (r"\bbuild\b|\bcompile\b|\bdist\b|\bbundle\b|\bwebpack\b|\bmake\b", "build"),
]

# Hard denylist: if a command's TEXT matches any of these, it is NEVER run, regardless of
# how it was named or classified. Network / deploy / publish / install / destructive.
DENY_PATTERNS: list[tuple[str, str]] = [
    (r"\bpublish\b", "publish step"),
    (r"\bdeploy\b", "deploy step"),
    (r"\brelease\b", "release step"),
    (r"\bnpm\s+publish\b|\byarn\s+publish\b|\bpnpm\s+publish\b", "package publish"),
    (r"\btwine\s+upload\b|\bpoetry\s+publish\b|\bcargo\s+publish\b|\bgem\s+push\b", "package publish"),
    (r"\bgit\s+push\b", "git push"),
    (r"\bpush\b.*\b(origin|remote|registry|docker|ghcr|ecr)\b", "push to remote/registry"),
    (r"\bdocker\s+push\b|\bdocker\s+login\b", "docker push/login"),
    (r"\bkubectl\b|\bhelm\s+(install|upgrade|delete)\b|\bterraform\s+(apply|destroy)\b", "infra deploy"),
    (r"\bnpm\s+(i|install|ci)\b|\byarn\s+install\b|\bpnpm\s+(i|install)\b|\bpip\s+install\b|\bpoetry\s+install\b", "dependency install"),
    (r"\bcurl\b|\bwget\b|\bnc\b|\bssh\b|\bscp\b|\brsync\b", "network transfer"),
    (r"\brm\s+-rf\b|\bmkfs\b|\bdd\s+if=|:\(\)\{", "destructive"),
    (r"\baws\s+(s3|ecr|lambda|deploy)\b|\bgcloud\s+\w+\s+deploy\b|\baz\s+\w+\s+create\b", "cloud action"),
]


def classify(name: str, command: str) -> str:
    """Return the check category, or "" if it does not match an allowed category."""

    hay_name = name.lower()
    hay_cmd = command.lower()
    for pattern, category in CATEGORY_KEYWORDS:
        if re.search(pattern, hay_name):
            return category
    for pattern, category in CATEGORY_KEYWORDS:
        if re.search(pattern, hay_cmd):
            return category
    return ""


def denied_reason(command: str) -> str:
    """Return a reason string if the command is denylisted, else ""."""

    hay = command.lower()
    for pattern, reason in DENY_PATTERNS:
        if re.search(pattern, hay):
            return reason
    return ""


# ---- Discovery -------------------------------------------------------------

@dataclass
class Check:
    """A discovered check command and its metadata."""

    name: str                 # human label, e.g. "npm:test" or "make:lint"
    command: list[str]        # argv to execute
    command_str: str          # display form
    source: str               # where it was discovered (package.json, Makefile, ...)
    category: str = ""        # test|lint|build|typecheck, or "" if unclassified
    eligible: bool = False    # classified into an allowed category AND not denied
    deny_reason: str = ""     # non-empty if denylisted


def _mk(name: str, argv: list[str], source: str, text: str) -> Check:
    deny = denied_reason(text)
    category = classify(name, text)
    return Check(
        name=name,
        command=argv,
        command_str=text,
        source=source,
        category=category,
        deny_reason=deny,
        eligible=bool(category) and not deny,
    )


def discover(root: Path) -> list[Check]:
    """Discover candidate checks from common repo manifests. PROPOSES only."""

    checks: list[Check] = []
    checks += _discover_package_json(root)
    checks += _discover_makefile(root)
    checks += _discover_pyproject_tox(root)
    checks += _discover_justfile(root)
    checks += _discover_ci(root)
    # De-duplicate by (name, command_str).
    seen: set[tuple[str, str]] = set()
    unique: list[Check] = []
    for c in checks:
        key = (c.name, c.command_str)
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return unique


def _discover_package_json(root: Path) -> list[Check]:
    path = root / "package.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    scripts = data.get("scripts", {}) or {}
    runner = "npm run"
    if (root / "pnpm-lock.yaml").is_file():
        runner = "pnpm run"
    elif (root / "yarn.lock").is_file():
        runner = "yarn"
    out: list[Check] = []
    for script_name, body in scripts.items():
        if not isinstance(body, str):
            continue
        text = f"{runner} {script_name}"
        # Classify using both the script name and the underlying script body (the body
        # is what actually runs, so a "ci" script that publishes is caught by denylist).
        argv = shlex.split(runner) + [script_name]
        c = _mk(f"npm:{script_name}", argv, "package.json", text)
        # Escalate deny/classification using the script body too.
        body_deny = denied_reason(body)
        if body_deny and not c.deny_reason:
            c.deny_reason = body_deny
            c.eligible = False
        if not c.category:
            c.category = classify(script_name, body)
            c.eligible = bool(c.category) and not c.deny_reason
        out.append(c)
    return out


def _discover_makefile(root: Path) -> list[Check]:
    out: list[Check] = []
    for fname in ("Makefile", "makefile", "GNUmakefile"):
        path = root / fname
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        # Match top-level targets: "name:" at column 0, not a variable assignment or
        # pattern rule. Capture the recipe's first line for denylist context.
        target_re = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*:(?!=)")
        for i, line in enumerate(lines):
            m = target_re.match(line)
            if not m:
                continue
            target = m.group(1)
            if target in ("PHONY", ".PHONY", "default", "all") and target.startswith("."):
                continue
            # Peek at the recipe body for denylist context.
            recipe = ""
            for j in range(i + 1, min(i + 8, len(lines))):
                if lines[j].startswith("\t"):
                    recipe += " " + lines[j].strip()
                elif lines[j].strip() and not lines[j].startswith("\t"):
                    break
            text = f"make {target}"
            c = _mk(f"make:{target}", ["make", target], fname, text)
            if not c.deny_reason:
                rd = denied_reason(recipe)
                if rd:
                    c.deny_reason, c.eligible = rd, False
            if not c.category:
                c.category = classify(target, recipe)
                c.eligible = bool(c.category) and not c.deny_reason
            out.append(c)
        break
    return out


def _discover_pyproject_tox(root: Path) -> list[Check]:
    out: list[Check] = []
    # tox environments
    tox = root / "tox.ini"
    if tox.is_file():
        try:
            text = tox.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for m in re.finditer(r"^\[testenv:([A-Za-z0-9._-]+)\]", text, re.MULTILINE):
            env = m.group(1)
            out.append(_mk(f"tox:{env}", ["tox", "-e", env], "tox.ini", f"tox -e {env}"))
        if re.search(r"^\[testenv\]", text, re.MULTILINE):
            out.append(_mk("tox", ["tox"], "tox.ini", "tox"))
    # A pyproject with pytest configured implies a runnable test suite.
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if "[tool.pytest" in text or "pytest" in text:
            out.append(_mk("pytest", ["pytest"], "pyproject.toml", "pytest"))
        if "[tool.ruff" in text:
            out.append(_mk("ruff:check", ["ruff", "check", "."], "pyproject.toml", "ruff check ."))
        if "[tool.mypy" in text:
            out.append(_mk("mypy", ["mypy", "."], "pyproject.toml", "mypy ."))
    return out


def _discover_justfile(root: Path) -> list[Check]:
    out: list[Check] = []
    for fname in ("justfile", "Justfile", ".justfile"):
        path = root / fname
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        recipe_re = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:[A-Za-z0-9_ ]*)?:")
        for line in lines:
            m = recipe_re.match(line)
            if not m:
                continue
            recipe = m.group(1)
            out.append(_mk(f"just:{recipe}", ["just", recipe], fname, f"just {recipe}"))
        break
    return out


def _discover_ci(root: Path) -> list[Check]:
    """Surface CI-declared run steps as PROPOSED, discovery-only context.

    CI YAML run steps are recorded so the reviewer can see what CI does, but they are NOT
    auto-run: CI steps often assume services/credentials. They are marked so the workflow
    can decide. We only extract obvious `run:` lines that classify as a check.
    """

    out: list[Check] = []
    ci_dir = root / ".github" / "workflows"
    if not ci_dir.is_dir():
        return out
    for path in sorted(ci_dir.glob("*.y*ml")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"^\s*(?:-\s*)?run:\s*(.+)$", text, re.MULTILINE):
            cmd = m.group(1).strip().strip("|>").strip()
            if not cmd or "\n" in cmd:
                continue
            category = classify("", cmd)
            if not category:
                continue  # only surface CI steps that look like checks
            rel = path.relative_to(root).as_posix()
            c = _mk(f"ci:{cmd[:40]}", shlex.split(cmd) if _safe_split(cmd) else [], rel, cmd)
            # CI steps are context-only: never eligible for auto-run (may need services).
            c.eligible = False
            out.append(c)
    return out


def _safe_split(cmd: str) -> bool:
    try:
        shlex.split(cmd)
        return True
    except ValueError:
        return False


# ---- Execution -------------------------------------------------------------

@dataclass
class Result:
    """The outcome of one check (ran or skipped)."""

    name: str
    command_str: str
    source: str
    category: str
    status: str               # passed | failed | timed-out | skipped
    exit_code: "int | None" = None
    duration_s: float = 0.0
    skip_reason: str = ""
    metrics: dict = field(default_factory=dict)
    log_excerpt: str = ""


LOG_EXCERPT_BYTES = 4000


def _extract_metrics(text: str) -> dict:
    """Best-effort scrape of common pass/fail/coverage numbers from tool output."""

    # Each pattern is anchored to real test-runner phrasing to avoid matching version
    # banners (e.g. "fix@1.0.0 test"). Metrics are best-effort context, never the verdict
    # (the verdict is the exit code); a bad scrape must not turn a fail into a pass.
    metrics: dict = {}
    m = re.search(r"(?<![.\d])(\d+)\s+passed\b", text)
    if m:
        metrics["passed"] = int(m.group(1))
    m = re.search(r"(?<![.\d])(\d+)\s+failed\b", text)
    if m:
        metrics["failed"] = int(m.group(1))
    m = re.search(r"(?<![.\d])(\d+)\s+errors?\b", text)
    if m:
        metrics["errors"] = int(m.group(1))
    # Explicit "Tests: N" (jest) or "collected N items" (pytest); not a bare "N test".
    m = re.search(r"(?:Tests:\s+|collected\s+)(\d+)\b", text)
    if m and "total_tests" not in metrics:
        metrics["total_tests"] = int(m.group(1))
    # coverage percentage (pytest-cov / jest / istanbul style "TOTAL ... 87%" or "87.5%")
    m = re.search(r"(?:TOTAL|All files|coverage)[^\n%]*?(\d{1,3}(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if m:
        metrics["coverage_pct"] = float(m.group(1))
    return metrics


def run_check(check: Check, root: Path, timeout: int) -> Result:
    """Execute one eligible check and capture evidence."""

    start = time.monotonic()
    try:
        proc = subprocess.run(
            check.command,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return Result(
            name=check.name, command_str=check.command_str, source=check.source,
            category=check.category, status="timed-out", exit_code=None,
            duration_s=round(time.monotonic() - start, 2),
            skip_reason=f"exceeded {timeout}s time bound",
            log_excerpt="(timed out)",
        )
    except (OSError, ValueError) as exc:
        return Result(
            name=check.name, command_str=check.command_str, source=check.source,
            category=check.category, status="skipped", exit_code=None,
            duration_s=round(time.monotonic() - start, 2),
            skip_reason=f"could not execute: {exc}",
        )
    duration = round(time.monotonic() - start, 2)
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    excerpt = combined.strip()
    if len(excerpt) > LOG_EXCERPT_BYTES:
        excerpt = excerpt[:LOG_EXCERPT_BYTES // 2] + "\n...[truncated]...\n" + excerpt[-LOG_EXCERPT_BYTES // 2:]
    return Result(
        name=check.name, command_str=check.command_str, source=check.source,
        category=check.category,
        status="passed" if proc.returncode == 0 else "failed",
        exit_code=proc.returncode,
        duration_s=duration,
        metrics=_extract_metrics(combined),
        log_excerpt=excerpt,
    )


# ---- Consent ---------------------------------------------------------------

def confirm(check: Check, assume_yes: bool) -> bool:
    """Decide whether to run a check. Denied is never run; unclassified needs explicit y."""

    if check.deny_reason:
        return False  # never
    if not check.category:
        # Unclassified: never auto-run; only an interactive explicit yes.
        if assume_yes:
            return False
        return _ask(f"Run UNCLASSIFIED command? [{check.name}] {check.command_str}")
    if assume_yes:
        return True  # eligible + allowlisted + --yes
    return _ask(f"Run {check.category} check? [{check.name}] {check.command_str}")


def _ask(prompt: str) -> bool:
    try:
        ans = input(f"{prompt}  (y/N) ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


# ---- Output ----------------------------------------------------------------

def summarize(results: list[Result]) -> dict:
    ran = [r for r in results if r.status in ("passed", "failed", "timed-out")]
    return {
        "discovered": len(results),
        "ran": len(ran),
        "passed": sum(1 for r in results if r.status == "passed"),
        "failed": sum(1 for r in results if r.status == "failed"),
        "timed_out": sum(1 for r in results if r.status == "timed-out"),
        "skipped": sum(1 for r in results if r.status == "skipped"),
        "all_ran_passed": bool(ran) and all(r.status == "passed" for r in ran),
    }


def emit(results: list[Result], fmt: str, out) -> None:
    s = summarize(results)
    honesty = (
        "This records only checks actually run. Skipped/denied/unclassified checks are "
        "NOT passes. A non-empty 'failed'/'timed_out', or 'ran' < number of relevant "
        "checks, means the result is not a full green."
    )
    if fmt == "json":
        json.dump(
            {"summary": s, "honesty_note": honesty, "results": [asdict(r) for r in results]},
            out, indent=2,
        )
        out.write("\n")
    elif fmt == "csv":
        import csv
        w = csv.writer(out)
        w.writerow(["name", "category", "status", "exit_code", "duration_s", "source",
                    "skip_reason", "metrics", "command"])
        for r in results:
            w.writerow([r.name, r.category, r.status, r.exit_code, r.duration_s, r.source,
                        r.skip_reason, json.dumps(r.metrics), r.command_str])
    else:
        out.write("Verify / check-run summary (evidence, not self-report)\n")
        out.write(f"  discovered: {s['discovered']}  ran: {s['ran']}  passed: {s['passed']}  "
                  f"failed: {s['failed']}  timed_out: {s['timed_out']}  skipped: {s['skipped']}\n")
        out.write(f"  all-ran-passed: {s['all_ran_passed']}\n\n")
        for r in results:
            line = f"  [{r.status:9}] {r.category or 'unclassified':12} {r.name:28} {r.command_str}"
            if r.exit_code is not None:
                line += f"  exit={r.exit_code}"
            if r.metrics:
                line += f"  {r.metrics}"
            if r.skip_reason:
                line += f"  ({r.skip_reason})"
            out.write(line + "\n")
        if not results:
            out.write("  no runnable checks discovered\n")
        out.write(f"\n  NOTE: {honesty}\n")


def _framework_version() -> str:
    """Return the agent-workflows framework version this tool ships with.

    VERSION lives at .agents/workflows/VERSION; this script is at
    .agents/workflows/verify/tools/run_checks.py, so it is three directories up.
    """

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


# ---- Main ------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Discover and run a repo's own checks; capture real evidence.",
    )
    ap.add_argument("--version", action="store_true", help="Print the framework version and exit.")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--format", choices=["json", "csv", "text"], default="text")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--list", action="store_true",
                    help="Only discover and list candidate checks; run nothing.")
    ap.add_argument("--yes", action="store_true",
                    help="Run all eligible (allowlisted) checks without per-check prompts.")
    ap.add_argument("--timeout", type=int, default=600,
                    help="Per-check time bound in seconds (default 600).")
    ap.add_argument("--only", default=None,
                    help="Comma-separated categories to consider: test,lint,build,typecheck.")
    ap.add_argument("--add", action="append", default=[],
                    help="Add an explicit command to consider (repeatable). Still classified/denied.")
    args = ap.parse_args()

    if args.version:
        print(_framework_version())
        return 0

    root = args.repo.expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    checks = discover(root)

    for raw in args.add:
        if not _safe_split(raw):
            print(f"Cannot parse --add command: {raw!r}", file=sys.stderr)
            continue
        checks.append(_mk(f"user:{raw[:40]}", shlex.split(raw), "--add", raw))

    if args.only:
        wanted = {c.strip().lower() for c in args.only.split(",") if c.strip()}
        checks = [c for c in checks if (c.category in wanted) or c.deny_reason or not c.category]

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout

    # --list: discovery only, run nothing.
    if args.list:
        results = [
            Result(name=c.name, command_str=c.command_str, source=c.source,
                   category=c.category, status="skipped",
                   skip_reason=(c.deny_reason and f"DENIED: {c.deny_reason}")
                   or ("unclassified" if not c.category else "discovery-only (--list)"))
            for c in checks
        ]
        emit(results, args.format, out)
        if args.out:
            out.close()
        return 0

    results: list[Result] = []
    for c in checks:
        if c.deny_reason:
            results.append(Result(
                name=c.name, command_str=c.command_str, source=c.source, category=c.category,
                status="skipped", skip_reason=f"DENIED (never run): {c.deny_reason}"))
            continue
        if not confirm(c, args.yes):
            reason = "declined" if not c.category and args.yes and False else (
                "unclassified; not run" if not c.category else "declined by user")
            results.append(Result(
                name=c.name, command_str=c.command_str, source=c.source, category=c.category,
                status="skipped", skip_reason=reason))
            continue
        results.append(run_check(c, root, args.timeout))

    emit(results, args.format, out)
    if args.out:
        out.close()

    s = summarize(results)
    if s["failed"] or s["timed_out"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
