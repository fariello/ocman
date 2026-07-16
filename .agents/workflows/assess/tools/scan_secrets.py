#!/usr/bin/env python3
"""
scan_secrets.py - read-only detector for committed secrets and sensitive data.

Recursively scans a repository's WORKING TREE and its GIT HISTORY for likely
secrets/credentials/keys and PII/PHI, so a review does not rely on an LLM crawling
millions of lines. It is deterministic, dependency-free (Python stdlib only), and
STRICTLY READ-ONLY: it never modifies the repo, never rotates or purges anything, and
never touches the network.

Findings are CANDIDATES, not verdicts - pattern and entropy detection is inherently
noisy. A human (or the `assess-secrets` / `release-review` workflow) triages them.

SAFETY: output NEVER contains a full secret value. Every match is redacted to a short
masked preview (e.g. "AKIA************WXYZ"). The report is therefore safe to save and
commit as a run artifact without itself becoming a leak.

Usage:
    python3 scan_secrets.py [--repo PATH] [--format json|csv|text]
                            [--working-tree-only] [--history-only]
                            [--max-commits N] [--since DATE]
                            [--max-file-bytes N] [--no-entropy] [--no-pii]
                            [--no-external] [--out FILE]

Exit codes: 0 = scan completed (regardless of findings; check the summary/counts),
            2 = usage/environment error.

By default it scans both the working tree and full git history. On very large repos,
bound history with --max-commits or --since, or use --working-tree-only.

If `gitleaks` or `trufflehog` is on PATH and --no-external is not set, their read-only
scans are also run and merged in (marked with source=gitleaks/trufflehog), redacted.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


# ---- Detection rules -------------------------------------------------------


# Each rule: (name, category, compiled regex, severity_hint). Regexes are designed to
# be reasonably specific to limit noise; the workflow triages the rest.
def _rules() -> list[tuple[str, str, "re.Pattern[str]", str]]:
    r = re.compile
    return [
        # --- Secrets / credentials / keys ---
        (
            "private-key-block",
            "secret",
            r(
                r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----"
            ),
            "high",
        ),
        (
            "aws-access-key-id",
            "secret",
            r(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA)[0-9A-Z]{16}\b"),
            "high",
        ),
        (
            "aws-secret-access-key",
            "secret",
            r(r"(?i)aws.{0,20}(?:secret|sk).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"),
            "high",
        ),
        (
            "gcp-service-account",
            "secret",
            r(r"\"type\"\s*:\s*\"service_account\""),
            "high",
        ),
        ("google-api-key", "secret", r(r"\bAIza[0-9A-Za-z\-_]{35}\b"), "high"),
        ("slack-token", "secret", r(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"), "high"),
        (
            "github-token",
            "secret",
            r(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[0-9A-Za-z_]{20,}\b"),
            "high",
        ),
        ("gitlab-token", "secret", r(r"\bglpat-[0-9A-Za-z\-_]{20}\b"), "high"),
        ("openai-key", "secret", r(r"\bsk-(?:proj-)?[0-9A-Za-z\-_]{20,}\b"), "high"),
        (
            "stripe-key",
            "secret",
            r(r"\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,}\b"),
            "high",
        ),
        ("twilio-key", "secret", r(r"\bSK[0-9a-fA-F]{32}\b"), "medium"),
        (
            "sendgrid-key",
            "secret",
            r(r"\bSG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}\b"),
            "high",
        ),
        ("npm-token", "secret", r(r"\bnpm_[0-9A-Za-z]{36}\b"), "high"),
        (
            "jwt",
            "secret",
            r(
                r"\beyJ[0-9A-Za-z_\-]{10,}\.eyJ[0-9A-Za-z_\-]{10,}\.[0-9A-Za-z_\-]{10,}\b"
            ),
            "medium",
        ),
        ("bearer-token", "secret", r(r"(?i)bearer\s+[0-9A-Za-z_\-\.=]{20,}"), "low"),
        (
            "basic-auth-url",
            "secret",
            r(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^/\s:@]+:[^/\s:@]+@[^/\s]+"),
            "high",
        ),
        (
            "password-assignment",
            "secret",
            r(
                r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?token|auth[_-]?token|client[_-]?secret)\s*[:=]\s*['\"][^'\"\n]{6,}['\"]"
            ),
            "medium",
        ),
        (
            "connection-string-pw",
            "secret",
            r(r"(?i)(?:Server|Data Source|Host)=[^;]+;.*(?:Password|Pwd)=[^;'\"]+"),
            "high",
        ),
        (
            "generic-secret-env",
            "secret",
            r(
                r"(?im)^(?:export\s+)?[A-Z0-9_]*(?:SECRET|TOKEN|APIKEY|API_KEY|PASSWORD|PASSWD|PRIVATE_KEY)[A-Z0-9_]*\s*=\s*\S{6,}"
            ),
            "low",
        ),
        # --- PII / PHI ---
        (
            "us-ssn",
            "pii",
            r(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"),
            "high",
        ),
        (
            "credit-card-candidate",
            "pii",
            r(r"\b(?:\d[ -]?){13,19}\b"),
            "medium",
        ),  # Luhn-checked below
        (
            "email",
            "pii",
            r(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
            "low",
        ),
        (
            "us-phone",
            "pii",
            r(r"\b(?:\+?1[ .\-]?)?\(?\d{3}\)?[ .\-]?\d{3}[ .\-]?\d{4}\b"),
            "low",
        ),
        ("iban", "pii", r(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), "low"),
        (
            "ipv4",
            "pii",
            r(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
            "low",
        ),
    ]


RULES = _rules()

# Path/segment skips - noise and irreversibly-large or generated content.
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".gradle",
    ".idea",
    ".terraform",
    "site-packages",
    ".next",
    ".cache",
    # Agent-workflow run records are generated deliverables (they may even contain a prior
    # scan's own redacted output); scanning them just re-flags noise, not committed secrets.
    "workflow-artifacts",
}
# Generated lockfiles are high-entropy hash soup, not human-authored secrets.
SKIP_FILENAME_SUFFIXES = (
    "-lock.json",
    ".lock.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "composer.lock",
)
# Binary/asset extensions we do not scan as text.
SKIP_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".bmp",
    ".tiff",
    ".svg",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".tgz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".wav",
    ".flac",
    ".ogg",
    ".webm",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".so",
    ".dylib",
    ".dll",
    ".class",
    ".o",
    ".a",
    ".jar",
    ".wasm",
    ".pyc",
    ".pyo",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".lock",
}
# Filenames that themselves warrant flagging (sensitive-file names).
SENSITIVE_FILENAMES = re.compile(
    r"(?i)(^|/)(\.env(\..+)?|\.npmrc|\.pypirc|\.netrc|id_rsa|id_dsa|id_ecdsa|id_ed25519|"
    r".*\.pem|.*\.pfx|.*\.p12|.*\.keystore|.*\.jks|.*service[-_]?account.*\.json|"
    r"credentials(\.json|\.yaml|\.yml)?|secrets(\.json|\.yaml|\.yml)?)$"
)

DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB per file


@dataclass
class Finding:
    rule: str
    category: str
    severity: str
    where: str  # "working-tree" or "history"
    location: str  # file path (+ ":line") or commit ref + path
    preview: str  # REDACTED
    source: str = "builtin"
    commit: str = ""
    extra: dict = field(default_factory=dict)


# ---- Helpers ---------------------------------------------------------------


def redact(match: str) -> str:
    """Return a safe, non-recoverable preview of a matched string."""

    s = match.strip()
    s = s.replace("\n", " ")
    if len(s) <= 8:
        return s[0] + "*" * (len(s) - 1) if s else ""
    # For short secrets (<16 chars) a 4+4 head/tail preview would reveal 8 of N chars - nearly the
    # whole value. Reveal at most the first 2 + last 2 there, so the "never a full secret" promise
    # holds for short tokens too (D85 F-tools). Longer secrets keep the 4+4 preview.
    if len(s) < 16:
        return f"{s[:2]}{'*' * (len(s) - 4)}{s[-2:]} (len={len(s)})"
    head = s[:4]
    tail = s[-4:]
    return f"{head}{'*' * min(12, max(4, len(s) - 8))}{tail} (len={len(s)})"


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def luhn_ok(digits: str) -> bool:
    d = [int(c) for c in digits if c.isdigit()]
    if not (13 <= len(d) <= 19):
        return False
    total = 0
    for i, x in enumerate(reversed(d)):
        if i % 2 == 1:
            x *= 2
            if x > 9:
                x -= 9
        total += x
    return total % 10 == 0


HIGH_ENTROPY_TOKEN = re.compile(r"[A-Za-z0-9+/=_\-]{20,}")


def is_probably_binary(data: bytes) -> bool:
    if b"\x00" in data[:4096]:
        return True
    # crude: too many non-text bytes
    sample = data[:4096]
    if not sample:
        return False
    text = sum(1 for b in sample if 9 <= b <= 13 or 32 <= b <= 126 or b >= 128)
    return (text / len(sample)) < 0.7


def scan_text(
    text: str,
    where: str,
    location: str,
    use_entropy: bool,
    use_pii: bool,
    commit: str = "",
    start_line: int = 1,
) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    for name, category, pattern, sev in RULES:
        if category == "pii" and not use_pii:
            continue
        for m in pattern.finditer(text):
            matched = m.group(0)
            if name == "credit-card-candidate" and not luhn_ok(matched):
                continue
            # Line number of the match, offset by start_line so a caller scanning a fragment
            # (e.g. a single added history line at a known target-file line) reports the real
            # line. Defaults to 1, so whole-file callers are unaffected.
            line_no = text.count("\n", 0, m.start()) + start_line
            loc = f"{location}:{line_no}"
            findings.append(
                Finding(
                    rule=name,
                    category=category,
                    severity=sev,
                    where=where,
                    location=loc,
                    preview=redact(matched),
                    commit=commit,
                )
            )
    if use_entropy:
        for i, line in enumerate(lines, start_line):
            for tok in HIGH_ENTROPY_TOKEN.findall(line):
                if len(tok) < 24:
                    continue
                ent = shannon_entropy(tok)
                if ent >= 4.0:
                    findings.append(
                        Finding(
                            rule="high-entropy-string",
                            category="secret",
                            severity="low",
                            where=where,
                            location=f"{location}:{i}",
                            preview=redact(tok),
                            commit=commit,
                            extra={"entropy": round(ent, 2)},
                        )
                    )
    return findings


# ---- Working-tree scan -----------------------------------------------------


def is_skipped_path(rel_posix: str) -> bool:
    """True if a repo-relative POSIX path is skipped noise (generated dir or lockfile).

    Shared by the working-tree and history scans so both exclude the same paths.
    Does NOT cover SKIP_EXTS (binary) - that is handled separately in the tree scan.
    """

    parts = set(rel_posix.split("/"))
    if parts & SKIP_DIR_NAMES:
        return True
    name = rel_posix.rsplit("/", 1)[-1]
    return name.endswith(SKIP_FILENAME_SUFFIXES)


def iter_tree_files(root: Path, max_bytes: int):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        if is_skipped_path(rel):
            continue
        if path.suffix.lower() in SKIP_EXTS:
            # still flag sensitive-named binary-ish files
            rel = path.relative_to(root).as_posix()
            if SENSITIVE_FILENAMES.search(rel):
                yield path, rel, None
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        yield path, path.relative_to(root).as_posix(), "text"


def scan_working_tree(
    root: Path, max_bytes: int, use_entropy: bool, use_pii: bool
) -> list[Finding]:
    findings: list[Finding] = []
    for path, rel, kind in iter_tree_files(root, max_bytes):
        if SENSITIVE_FILENAMES.search(rel):
            findings.append(
                Finding(
                    rule="sensitive-filename",
                    category="secret",
                    severity="medium",
                    where="working-tree",
                    location=rel,
                    preview="(file name matches a sensitive pattern)",
                )
            )
        if kind != "text":
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if is_probably_binary(data):
            continue
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            continue
        findings.extend(scan_text(text, "working-tree", rel, use_entropy, use_pii))
    return findings


# ---- Git history scan ------------------------------------------------------


def is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def git(root: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )


def scan_history(
    root: Path,
    max_commits: int | None,
    since: str | None,
    use_entropy: bool,
    use_pii: bool,
    max_bytes: int,
) -> list[Finding]:
    """Scan added lines across history via `git log -p`. Redacted, bounded."""

    findings: list[Finding] = []
    args = [
        "log",
        "-p",
        "--no-color",
        "--no-merges",
        "-U0",
        "--pretty=format:%H%x00%aI%x00%s",
    ]
    if max_commits:
        args += [f"-n{max_commits}"]
    if since:
        args += [f"--since={since}"]
    proc = git(root, args)
    if proc.returncode != 0:
        return findings

    commit = ""
    cur_file = ""
    line_no = 0  # current target-file line number of the next added line in the hunk
    for raw in proc.stdout.splitlines():
        if "\x00" in raw and re.match(r"^[0-9a-f]{7,40}\x00", raw):
            commit = raw.split("\x00", 1)[0]
            cur_file = ""
            continue
        if raw.startswith("+++ b/"):
            cur_file = raw[6:]
            line_no = 0
            continue
        if raw.startswith("@@"):
            # Hunk header: @@ -a,b +c,d @@ -> added lines start at target line c.
            m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
            line_no = int(m.group(1)) if m else 0
            continue
        if cur_file and is_skipped_path(cur_file):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            added = raw[1:]
            # Scan just this added line, telling scan_text its real target-file line number
            # so history findings report the exact line instead of :1.
            for f in scan_text(
                added,
                "history",
                f"{commit[:10]}:{cur_file}",
                use_entropy,
                use_pii,
                commit=commit,
                start_line=line_no if line_no else 1,
            ):
                findings.append(f)
            if line_no:
                line_no += 1
    return findings


# ---- Optional external scanners -------------------------------------------

# Mature, dedicated scanners this tool will use if present, and how to install them.
# This built-in scanner is a dependency-free safety net, NOT a replacement for these.
EXTERNAL_TOOLS = {
    "gitleaks": "https://github.com/gitleaks/gitleaks  (brew install gitleaks | go install github.com/gitleaks/gitleaks/v8@latest)",
    "trufflehog": "https://github.com/trufflesecurity/trufflehog  (brew install trufflehog | pipx install trufflehog3)",
    "detect-secrets": "https://github.com/Yelp/detect-secrets  (pipx install detect-secrets | pip install detect-secrets)",
}


def tool_availability() -> dict[str, bool]:
    """Return which recommended external scanners are on PATH."""

    return {name: _which(name) for name in EXTERNAL_TOOLS}


def install_recommendations(avail: dict[str, bool]) -> list[str]:
    """Human-readable install suggestions for any missing mature scanners."""

    return [
        f"{name}: {EXTERNAL_TOOLS[name]}"
        for name, present in avail.items()
        if not present
    ]


def run_external(root: Path, avail: dict[str, bool]) -> list[Finding]:
    findings: list[Finding] = []
    # gitleaks (read-only detect)
    if avail.get("gitleaks"):
        p = subprocess.run(
            [
                "gitleaks",
                "detect",
                "--source",
                str(root),
                "--report-format",
                "json",
                "--report-path",
                "/dev/stdout",
                "--no-banner",
            ],
            capture_output=True,
            text=True,
        )
        try:
            for item in json.loads(p.stdout or "[]"):
                findings.append(
                    Finding(
                        rule=item.get("RuleID", "gitleaks"),
                        category="secret",
                        severity="high",
                        where="history" if item.get("Commit") else "working-tree",
                        location=f"{item.get('File','')}:{item.get('StartLine','')}",
                        preview=redact(str(item.get("Secret", item.get("Match", "")))),
                        source="gitleaks",
                        commit=str(item.get("Commit", "")),
                    )
                )
        except (ValueError, TypeError):
            pass
    return findings


def _which(name: str) -> bool:
    from shutil import which

    return which(name) is not None


# ---- Output ----------------------------------------------------------------


def summarize(findings: list[Finding]) -> dict:
    by_cat: dict[str, int] = {}
    by_sev: dict[str, int] = {}
    by_where: dict[str, int] = {}
    for f in findings:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_where[f.where] = by_where.get(f.where, 0) + 1
    return {
        "total": len(findings),
        "by_category": by_cat,
        "by_severity": by_sev,
        "by_location": by_where,
    }


def emit(
    findings: list[Finding],
    fmt: str,
    out,
    avail: dict[str, bool],
    skipped_external: bool = False,
) -> None:
    recs = install_recommendations(avail)
    used = [n for n, p in avail.items() if p]
    have_mature = bool(used)
    if fmt == "json":
        if have_mature:
            note = (
                "This built-in scanner is a dependency-free safety net. A mature "
                "scanner is installed and was run alongside it."
            )
        elif skipped_external:
            note = (
                "This built-in scanner is a dependency-free safety net. External "
                "scanners were skipped (--no-external); none were run this pass."
            )
        else:
            note = (
                "This built-in scanner is a dependency-free safety net. For production "
                "assurance, install and run a mature, actively-maintained scanner too."
            )
        json.dump(
            {
                "summary": summarize(findings),
                "external_tools": {
                    "available": used,
                    "missing_recommended": [n for n, p in avail.items() if not p],
                    "install": {
                        n: EXTERNAL_TOOLS[n] for n in EXTERNAL_TOOLS if not avail.get(n)
                    },
                },
                "note": note,
                "findings": [asdict(f) for f in findings],
            },
            out,
            indent=2,
        )
        out.write("\n")
    elif fmt == "csv":
        import csv

        w = csv.writer(out)
        w.writerow(
            [
                "rule",
                "category",
                "severity",
                "where",
                "commit",
                "location",
                "preview",
                "source",
            ]
        )
        for f in findings:
            w.writerow(
                [
                    f.rule,
                    f.category,
                    f.severity,
                    f.where,
                    f.commit,
                    f.location,
                    f.preview,
                    f.source,
                ]
            )
    else:
        s = summarize(findings)
        out.write("Secret/PII scan summary (candidates - triage required)\n")
        out.write(
            f"  total: {s['total']}  by_severity: {s['by_severity']}  "
            f"by_category: {s['by_category']}  by_location: {s['by_location']}\n\n"
        )
        for f in findings:
            out.write(
                f"  [{f.severity:6}] {f.category:6} {f.rule:24} {f.where:12} "
                f"{f.location}  {f.preview}\n"
            )
        if not findings:
            out.write("  no candidates found\n")

    # Tool-maturity guidance (printed to stderr for text/csv so it never corrupts the
    # machine-readable stream; embedded in the JSON object for json).
    if fmt != "json":
        msg = [
            "",
            "External scanner status (this built-in scanner is a safety net, not a replacement):",
        ]
        msg.append(f"  used: {', '.join(used) if used else 'none'}")
        if have_mature:
            # A mature scanner is present and was run; do not nag to install one. Only
            # mention any others as optional additional coverage.
            if recs:
                msg.append(
                    "  optional - additional scanners available for broader coverage:"
                )
                msg.extend(f"    - {r}" for r in recs)
        elif skipped_external:
            msg.append(
                "  external scanners skipped (--no-external); install status not checked this pass."
            )
        elif recs:
            msg.append(
                "  RECOMMENDED - install a mature scanner for stronger assurance:"
            )
            msg.extend(f"    - {r}" for r in recs)
        print("\n".join(msg), file=sys.stderr)


def _framework_version() -> str:
    """Return the agent-workflows framework version this tool ships with.

    The VERSION file lives at the framework root (.agents/workflows/VERSION); this script
    is at .agents/workflows/assess/tools/scan_secrets.py, so it is three directories up.
    Returns "unknown" if the file is absent (e.g. run standalone outside the framework).
    """

    version_path = Path(__file__).resolve().parent.parent.parent / "VERSION"
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return value or "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read-only secrets/PII scanner (tree + git history)."
    )
    ap.add_argument(
        "--version",
        action="store_true",
        help="Print the agent-workflows framework version and exit.",
    )
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--format", choices=["json", "csv", "text"], default="text")
    ap.add_argument("--working-tree-only", action="store_true")
    ap.add_argument("--history-only", action="store_true")
    ap.add_argument("--max-commits", type=int, default=None)
    ap.add_argument("--since", default=None)
    ap.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    ap.add_argument("--no-entropy", action="store_true")
    ap.add_argument("--no-pii", action="store_true")
    ap.add_argument("--no-external", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.version:
        print(_framework_version())
        return 0

    root = args.repo.expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    use_entropy = not args.no_entropy
    use_pii = not args.no_pii
    findings: list[Finding] = []

    if not args.history_only:
        findings += scan_working_tree(root, args.max_file_bytes, use_entropy, use_pii)

    if not args.working_tree_only:
        if is_git_repo(root):
            findings += scan_history(
                root,
                args.max_commits,
                args.since,
                use_entropy,
                use_pii,
                args.max_file_bytes,
            )
        elif args.history_only:
            print("Not a git repository; cannot scan history.", file=sys.stderr)
            return 2

    avail = (
        tool_availability()
        if not args.no_external
        else {n: False for n in EXTERNAL_TOOLS}
    )
    if not args.no_external:
        try:
            findings += run_external(root, avail)
        except Exception:
            pass  # external tools are best-effort

    # newline="" so the csv module controls line endings (no double-blank rows on Windows).
    out = open(args.out, "w", encoding="utf-8", newline="") if args.out else sys.stdout
    try:
        emit(findings, args.format, out, avail, skipped_external=args.no_external)
    finally:
        if args.out:
            out.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
