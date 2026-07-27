#!/usr/bin/env python3
"""
conformance_harness.py - deterministic harness for host delivery conformance probes.

This tool provides the deterministic half of Phase 0 host delivery conformance testing:
1. Isolated fixture scaffolder: builds a clean temp $HOME, an empty temp git repo,
   external content outside the repo, tier fixtures (T1/T2/T3/precedence), and a unique nonce.
   Enforces strict isolation guards so real user home and host configs are never touched.
2. Per-host command/diagnostic renderer: produces exact environment exports, execution
   commands, and diagnostic queries per host x tier x variant from a seeded host matrix data file.
3. Results recorder & validator: ingests operator observations and enforces Resolved vs.
   Followed verification discipline into durable 9-point research reports.

Safety:
- NEVER writes to the real $HOME directory or real host config.
- Refuses to scaffold if the base directory is or parents the real home directory, or if
  any written path escapes the base directory.
- Requires operator host launches to execute under rendered HOME/XDG environment variables.
"""

from __future__ import annotations

import argparse
import datetime
import json
import secrets
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_MATRIX_PATH = Path(__file__).resolve().parent / "host_matrix.json"


# ---- Safety & Isolation Guard ----------------------------------------------


class SafetyError(ValueError):
    """Raised when an operation violates isolation safety guards."""

    pass


def assert_isolated_base(base_dir: Path | str) -> Path:
    """Validate and resolve the base directory for fixture scaffolding.

    Must NOT be empty/None, must NOT be equal to real home, must NOT be a parent of real home.
    Returns the resolved absolute Path object.
    """
    if not base_dir:
        raise SafetyError("Base directory argument is required (cannot be empty).")

    base_path = Path(base_dir).resolve()
    real_home = Path.home().resolve()

    if base_path == real_home:
        raise SafetyError(
            f"Isolation guard violation: Base directory '{base_path}' cannot be the real home directory '{real_home}'."
        )

    if base_path in real_home.parents:
        raise SafetyError(
            f"Isolation guard violation: Base directory '{base_path}' is a parent of real home directory '{real_home}'."
        )

    fixture_home = (base_path / "home").resolve()
    if fixture_home == real_home:
        raise SafetyError(
            f"Isolation guard violation: Fixture home '{fixture_home}' equals real home directory '{real_home}'."
        )

    if fixture_home in real_home.parents:
        raise SafetyError(
            f"Isolation guard violation: Fixture home '{fixture_home}' is a parent of real home directory '{real_home}'."
        )

    return base_path


def assert_contained(target_path: Path | str, base_dir: Path | str) -> Path:
    """Ensure target_path resolves strictly within base_dir.

    Raises SafetyError if target_path escapes base_dir.
    """
    base_res = Path(base_dir).resolve()
    target_res = Path(target_path).resolve()

    try:
        target_res.relative_to(base_res)
    except ValueError:
        raise SafetyError(
            f"Isolation guard violation: Path '{target_res}' escapes base directory '{base_res}'."
        )

    return target_res


# ---- Fixture Scaffolder ----------------------------------------------------


@dataclass
class FixtureResult:
    base_dir: str
    fixture_home: str
    target_repo: str
    external_content: str
    tier: str
    host: str
    version: str
    nonce: str
    probe_filename: str
    fixture_path: str
    env_vars: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scaffold(
    base_dir: Path | str,
    host: str,
    version: str,
    tier: str = "T2",
    nonce: str | None = None,
    matrix_path: Path | None = None,
) -> FixtureResult:
    """Build an isolated fixture tree for a host/version/tier probe run."""
    base_path = assert_isolated_base(base_dir)

    if not nonce:
        nonce = secrets.token_hex(4)

    fixture_home = assert_contained(base_path / "home", base_path)
    target_repo = assert_contained(base_path / "target_repo", base_path)
    external_content = assert_contained(base_path / "external_content", base_path)
    xdg_config = assert_contained(fixture_home / ".config", base_path)
    xdg_data = assert_contained(fixture_home / ".local" / "share", base_path)
    xdg_cache = assert_contained(fixture_home / ".cache", base_path)

    # Create directory tree
    for d in (
        fixture_home,
        target_repo,
        external_content,
        xdg_config,
        xdg_data,
        xdg_cache,
    ):
        d.mkdir(parents=True, exist_ok=True)

    # Initialize empty git repo in target_repo
    git_dir = target_repo / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init", "-q"],
                cwd=str(target_repo),
                check=True,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError) as e:
            raise RuntimeError(
                f"Failed to initialize git repository at {target_repo}: {e}"
            )

    probe_filename = f"PROBE-OK-{host}-{version}-{nonce}.txt"
    instruction = (
        f"CONFORMANCE PROBE INSTRUCTION:\n"
        f"Create a file named '{probe_filename}' in the target repository root containing exactly the nonce string '{nonce}'.\n"
    )

    matrix = load_host_matrix(matrix_path)
    hosts_data = matrix.get("hosts", {})
    host_info = hosts_data.get(host, {})

    tier_upper = tier.upper()
    fixture_path: Path

    if tier_upper == "T1":
        # Out-of-repo pointer fixture in external_content
        pointer_dir = assert_contained(external_content / "pointers", base_path)
        pointer_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = assert_contained(pointer_dir / "probe_pointer.md", base_path)
        fixture_path.write_text(instruction, encoding="utf-8")
    elif tier_upper == "T3":
        # Global location under fixture_home
        t3_rel = host_info.get("t3_global", {}).get(
            "global_path", ".config/skills/probe/SKILL.md"
        )
        t3_rel = t3_rel.replace("{skill_name}", "conformance_probe")
        fixture_path = assert_contained(fixture_home / t3_rel, base_path)
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(instruction, encoding="utf-8")
    else:
        # Default T2: skill layout
        t2_rel = host_info.get("t2_layout", {}).get(
            "preferred_path", ".agents/skills/{skill_name}/SKILL.md"
        )
        t2_rel = t2_rel.replace("{skill_name}", "conformance_probe")
        # For T2, place fixture in target_repo preferred path and external_content
        fixture_path = assert_contained(target_repo / t2_rel, base_path)
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(instruction, encoding="utf-8")

        ext_skill = assert_contained(
            external_content / "skills" / "conformance_probe" / "SKILL.md", base_path
        )
        ext_skill.parent.mkdir(parents=True, exist_ok=True)
        ext_skill.write_text(instruction, encoding="utf-8")

    env_vars = {
        "HOME": str(fixture_home),
        "XDG_CONFIG_HOME": str(xdg_config),
        "XDG_DATA_HOME": str(xdg_data),
        "XDG_CACHE_HOME": str(xdg_cache),
    }

    return FixtureResult(
        base_dir=str(base_path),
        fixture_home=str(fixture_home),
        target_repo=str(target_repo),
        external_content=str(external_content),
        tier=tier_upper,
        host=host,
        version=version,
        nonce=nonce,
        probe_filename=probe_filename,
        fixture_path=str(fixture_path),
        env_vars=env_vars,
    )


# ---- Host Matrix & Renderer ------------------------------------------------


def load_host_matrix(matrix_path: Path | None = None) -> dict[str, Any]:
    path = matrix_path or DEFAULT_MATRIX_PATH
    if not path.exists():
        raise FileNotFoundError(f"Host matrix file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in host matrix file {path}: {e}")


@dataclass
class RenderedCommands:
    host: str
    version: str
    tier: str
    variant: str
    env_exports: list[str]
    host_command: str
    diagnostic_commands: list[str]
    side_effect_check: str
    script_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_commands(
    host: str,
    version: str,
    tier: str,
    base_dir: Path | str,
    nonce: str,
    variant: str = "default",
    matrix_path: Path | None = None,
) -> RenderedCommands:
    """Render operator execution commands and diagnostics from the host matrix."""
    matrix = load_host_matrix(matrix_path)
    hosts_data = matrix.get("hosts", {})

    if host not in hosts_data:
        known = ", ".join(sorted(hosts_data.keys()))
        raise ValueError(f"Unknown host '{host}'. Supported hosts in matrix: {known}")

    host_info = hosts_data[host]
    base_path = assert_isolated_base(base_dir)
    fixture_home = base_path / "home"
    target_repo = base_path / "target_repo"
    probe_filename = f"PROBE-OK-{host}-{version}-{nonce}.txt"

    env_exports = [
        f"export HOME={fixture_home}",
        f"export XDG_CONFIG_HOME={fixture_home}/.config",
        f"export XDG_DATA_HOME={fixture_home}/.local/share",
        f"export XDG_CACHE_HOME={fixture_home}/.cache",
    ]

    cmd_template = host_info.get("command_template", "{host} run --cwd {target_repo}")
    fixture_rel = f"tier-{tier.lower()}"
    raw_cmd = cmd_template.format(
        host=host,
        target_repo=target_repo,
        tier_fixture=fixture_rel,
    )

    if variant == "noninteractive":
        raw_cmd += " --non-interactive"
    elif variant == "approval-accepted":
        raw_cmd += " --auto-approve"
    elif variant == "permission-denied":
        raw_cmd += " --deny-permissions"
    elif variant == "precedence":
        raw_cmd += " --check-precedence"

    diag_cmds = host_info.get("diagnostic_commands", [])
    side_effect_check = (
        f"test -f {target_repo}/{probe_filename} && cat {target_repo}/{probe_filename}"
    )

    script_lines = [
        f"# --- Host Probe Execution Script for {host_info.get('display_name', host)} ({version}) ---",
        f"# Tier: {tier.upper()} | Variant: {variant} | Nonce: {nonce}",
        "# Step 1: Export isolated environment",
        *env_exports,
        "# Step 2: Run host command",
        f"cd {target_repo}",
        raw_cmd,
        "# Step 3: Run host diagnostic queries",
        *diag_cmds,
        "# Step 4: Verify expected nonce side effect",
        side_effect_check,
    ]

    return RenderedCommands(
        host=host,
        version=version,
        tier=tier.upper(),
        variant=variant,
        env_exports=env_exports,
        host_command=raw_cmd,
        diagnostic_commands=diag_cmds,
        side_effect_check=side_effect_check,
        script_text="\n".join(script_lines),
    )


# ---- Results Recorder & Validator ------------------------------------------


@dataclass
class OperatorObservation:
    host: str
    version: str
    tier: str
    variant: str
    nonce: str
    resolved: bool
    diagnostic_evidence: str
    followed: bool
    nonce_side_effect_file: str
    side_effect_verified: bool
    operator: str
    timestamp: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()


def validate_observation(obs: OperatorObservation) -> None:
    """Enforce strict Resolved vs. Followed verification discipline."""
    if obs.followed:
        if not obs.side_effect_verified:
            raise ValueError(
                "Validation failed: 'Followed' cannot be marked True without side_effect_verified=True."
            )
        if not obs.nonce_side_effect_file or not obs.nonce_side_effect_file.startswith(
            "PROBE-OK-"
        ):
            raise ValueError(
                "Validation failed: 'Followed' cannot be marked True without a valid PROBE-OK-* nonce side-effect file recorded."
            )

    if obs.resolved:
        if not obs.diagnostic_evidence or len(obs.diagnostic_evidence.strip()) < 10:
            raise ValueError(
                "Validation failed: 'Resolved' cannot be marked True without concrete diagnostic evidence (at least 10 chars)."
            )

    if obs.followed and not obs.resolved:
        raise ValueError(
            "Validation failed: 'Followed' requires 'Resolved' to be True (a host cannot follow content it failed to resolve)."
        )


def generate_results_report(observations: list[OperatorObservation]) -> str:
    """Generate durable Markdown results report with all 9 recipe fields."""
    for obs in observations:
        validate_observation(obs)

    lines = [
        "# Conformance Probe Results Report",
        "",
        f"- Generated At: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"- Total Probes Recorded: {len(observations)}",
        "",
        "## Required Release Fixture Summary Table (9-Point Recipe)",
        "",
        "| Host & Version | Tier & Variant | Nonce | Isolated Fixture | Environment (HOME) | Resolved? | Followed? | Side-Effect File | Verified By |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for obs in observations:
        res_str = "YES" if obs.resolved else "NO"
        fol_str = "YES" if obs.followed else "NO"
        side_file = obs.nonce_side_effect_file or "(none)"
        lines.append(
            f"| {obs.host} v{obs.version} | {obs.tier} ({obs.variant}) | {obs.nonce} | clean temp base | {obs.host}-isolated | {res_str} | {fol_str} | {side_file} | {obs.operator} |"
        )

    lines.extend(
        [
            "",
            "## Detailed Probe Records",
            "",
        ]
    )

    for idx, obs in enumerate(observations, 1):
        lines.extend(
            [
                f"### Probe #{idx}: {obs.host} ({obs.version}) - {obs.tier} [{obs.variant}]",
                "",
                f"- **Host**: {obs.host} v{obs.version}",
                f"- **Tier & Variant**: {obs.tier} ({obs.variant})",
                f"- **Nonce**: {obs.nonce}",
                f"- **Operator**: {obs.operator}",
                f"- **Timestamp**: {obs.timestamp}",
                f"- **Classification**: Resolved={obs.resolved}, Followed={obs.followed}",
                f"- **Nonce Side-Effect File**: {obs.nonce_side_effect_file or 'None'}",
                f"- **Side-Effect Verified**: {obs.side_effect_verified}",
                "- **Diagnostic Evidence**:",
                "```",
                obs.diagnostic_evidence.strip() or "(no diagnostic evidence recorded)",
                "```",
                f"- **Notes**: {obs.notes or 'None'}",
                "",
            ]
        )

    return "\n".join(lines)


# ---- CLI Dispatch ----------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="conformance_harness",
        description="Phase 0 Conformance Harness for Host Delivery Probes",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: scaffold
    p_scaffold = sub.add_parser(
        "scaffold", help="Scaffold an isolated probe fixture tree"
    )
    p_scaffold.add_argument(
        "--base", required=True, help="REQUIRED base directory (must not be real home)"
    )
    p_scaffold.add_argument(
        "--host", required=True, help="Host ID (e.g. opencode, claude_code)"
    )
    p_scaffold.add_argument(
        "--version", required=True, help="Host version (e.g. 1.0.0)"
    )
    p_scaffold.add_argument(
        "--tier", default="T2", choices=["T1", "T2", "T3"], help="Delivery tier"
    )
    p_scaffold.add_argument("--nonce", help="Optional nonce string")

    # Subcommand: render
    p_render = sub.add_parser("render", help="Render execution and diagnostic commands")
    p_render.add_argument("--host", required=True, help="Host ID")
    p_render.add_argument("--version", required=True, help="Host version")
    p_render.add_argument("--tier", default="T2", help="Delivery tier")
    p_render.add_argument("--base", required=True, help="Base directory")
    p_render.add_argument("--nonce", required=True, help="Nonce string")
    p_render.add_argument(
        "--variant", default="default", help="Variant (default, noninteractive, etc.)"
    )

    # Subcommand: validate-json
    p_validate = sub.add_parser(
        "validate-json", help="Validate operator observation JSON"
    )
    p_validate.add_argument(
        "--file", required=True, help="JSON file containing observations list"
    )

    args = parser.parse_args(argv)

    try:
        if args.subcommand == "scaffold":
            res = scaffold(
                base_dir=args.base,
                host=args.host,
                version=args.version,
                tier=args.tier,
                nonce=args.nonce,
            )
            print(json.dumps(res.to_dict(), indent=2))
            return 0

        elif args.subcommand == "render":
            cmds = render_commands(
                host=args.host,
                version=args.version,
                tier=args.tier,
                base_dir=args.base,
                nonce=args.nonce,
                variant=args.variant,
            )
            print(cmds.script_text)
            return 0

        elif args.subcommand == "validate-json":
            path = Path(args.file)
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = [data]
            obs_list = [OperatorObservation(**item) for item in data]
            report = generate_results_report(obs_list)
            print(report)
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
