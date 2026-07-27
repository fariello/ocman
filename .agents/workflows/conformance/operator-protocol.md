# Host Conformance Probe Operator Protocol (Runbook)

- Purpose: Operator runbook for running host delivery probes and gathering durable evidence.
- Status: Phase 0 Deterministic Protocol
- Authoritative Rule: No clean-delta or skills delivery tier (T1 out-of-repo pointer, T2 skill, T3 global, fallback) may ship until a live per-host/version probe reproduces the documented behavior.

> [!CAUTION]
> ISOLATION SAFETY MANDATE: Probes MUST run against a clean temp `$HOME` rendered by the scaffolder tool. NEVER run probes against your real user home directory (`~`) or allow a host to mutate your real host configuration. The scaffolder enforces safety guards and will raise an error if pointed at real home.

## Protocol Overview

The host conformance probe protocol consists of 4 steps:

```
Step 1: Scaffold Isolated Fixture -> Step 2: Run Rendered Host Commands -> Step 3: Diagnostic Check & Side-Effect Verification -> Step 4: Record & Validate Evidence Report
```

## Step-by-Step Operator Procedure

### Step 1: Scaffold an Isolated Fixture

Run the scaffolder to build a clean base directory containing a clean temp `$HOME`, an empty target git repository, external content, and a unique nonce:

```bash
python3 .agents/workflows/conformance/tools/conformance_harness.py scaffold \
  --base /tmp/probe-<host>-<tier> \
  --host <host_id> \
  --version <host_version> \
  --tier <T1|T2|T3>
```

Parameters:
- `--base`: Base directory for the probe run (MUST be under `/tmp` or a scratch directory, NEVER your real `$HOME`).
- `--host`: Host identifier (`opencode`, `claude_code`, `codex`, `copilot`, `cursor`, `antigravity`, `gemini_cli`).
- `--version`: Installed version of the host CLI or application.
- `--tier`: Target delivery tier (`T1` out-of-repo pointer, `T2` skill layout, `T3` global location).

### Step 2: Render & Execute Host Commands

Render the exact environment setup, execution commands, and diagnostic queries for the scaffolded fixture:

```bash
python3 .agents/workflows/conformance/tools/conformance_harness.py render \
  --base /tmp/probe-<host>-<tier> \
  --host <host_id> \
  --version <host_version> \
  --tier <T1|T2|T3> \
  --nonce <nonce_from_step_1> \
  --variant <default|noninteractive|approval-accepted|permission-denied|precedence>
```

Copy and execute the rendered script block in your terminal. Ensure that:
1. `HOME` and `XDG_CONFIG_HOME` environment variables are exported before launching the host.
2. The host runs strictly inside the isolated target repository.

### Step 3: Record Diagnostics and Verify Nonce Side-Effect

After running the host command, observe and record two distinct verification outcomes:

1. **Resolved Verification**:
   - Run the rendered diagnostic queries (e.g. `opencode list-skills`, `claude doctor`, `agy list-skills`).
   - Check host logs or context output to confirm the host loaded or attached the instruction content.
   - Capture the exact diagnostic output text.

2. **Followed Verification**:
   - Check if the host created the expected nonce side-effect file in the target repository root:
     `PROBE-OK-<host>-<version>-<nonce>.txt`
   - Verify that the file exists AND contains the exact nonce string.

### Step 4: Record & Validate Evidence into Durable Report

Format your observation record as JSON or invoke the Python validator API.

Example observation JSON format (`observation.json`):

```json
[
  {
    "host": "opencode",
    "version": "1.0.0",
    "tier": "T2",
    "variant": "default",
    "nonce": "<nonce>",
    "resolved": true,
    "diagnostic_evidence": "OpenCode context loaded skill conformance_probe successfully.",
    "followed": true,
    "nonce_side_effect_file": "PROBE-OK-opencode-1.0.0-<nonce>.txt",
    "side_effect_verified": true,
    "operator": "<operator_name>",
    "notes": "Loaded without user prompts in default configuration."
  }
]
```

Validate and generate the durable Markdown report:

```bash
python3 .agents/workflows/conformance/tools/conformance_harness.py validate-json --file observation.json
```

Save the generated report under `.agents/docs/research/YYYYMMDD-HHMM-NN-conformance-results-<host>.md` to immortalize the evidence gating decision.
