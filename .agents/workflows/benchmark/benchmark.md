# Benchmark (guided performance-benchmarking setup and run)

Treat this file as the controlling instruction for a **guided, wizard-style** workflow
that helps a repository **gather performance information**: it authors an isolated
benchmark suite in the target repo, captures the machine/environment deeply, diagnoses
known good/bad configurations, runs the benchmarks with proper warm-up, optionally
submits to an HPC scheduler, and produces a shareable results bundle.

This is **informational by default**, not a regression gate. Performance numbers are noisy
and environment-bound; the goal is to understand performance and its context, not to fail
a build. An **optional** baseline-comparison mode exists for users who explicitly want a
guardrail (see Step 7); it is opt-in and never breaks CI unless the user wires it in.

It shares this framework's policies rather than restating them:

- **Fix Bar:** `../release-review/fix-decision-policy.md` (fix by default; defer only at
  Medium-High-or-higher Remediation Risk). Applied here to the benchmark suite and the
  environment remedies proposed, not to the project's product code.
- **Personas:** `../release-review/00-run-protocol.md`, led here by the software engineer,
  the performance-minded architect, and the operator/HPC user.

If those files are absent (this workflow copied alone), apply the same rules from memory.

## Operating principles (MUST)

- **Ask before each change.** Present each proposed change (a new benchmark file, a config
  remedy, an HPC submission), explain why, and wait for yes/no/skip. Never batch-apply.
- **Isolation is the contract.** The benchmark suite MUST live in a dedicated `benchmarks/`
  directory (or the repo's existing convention) that ships NO import into the product, adds
  NO runtime cost when unused, and installs NO hooks into the product. The product must
  behave identically whether or not `benchmarks/` exists. This is how we honor "including
  benchmarking has zero effect on the project's performance": the *inclusion* is inert.
- **Honest about measurement cost.** Observing performance is not free. We minimize it by
  timing out-of-process (subprocess/CLI level) rather than instrumenting the product
  in-process, and we say so. Do NOT claim a literal 0% measurement overhead - that is not
  true of any harness. The 0% guarantee is about *inclusion*, not *observation*.
- **Read-only on system state.** The environment tool and this workflow NEVER change CPU
  governors, mounts, swap, or system settings. They READ deeply and SUGGEST remedies as
  copy-pasteable commands for the user to run. The only writes are inside the benchmark's
  own scratch/output dirs and the run record.
- **Consent gates every execution.** Running the benchmarks executes repo code; submitting
  to a cluster affects shared resources. Both require explicit confirmation. HPC submission
  is confirmed PER SUBMISSION and is never triggered by any batch/`--yes` flag.
- **Stage, do not commit** (unless asked). Never push. Never publish results anywhere; the
  tool makes no network calls. Sharing is the user's explicit action.
- **KISS.** Prefer the simplest correct benchmark that answers the performance question.
  Do not gold-plate the suite. No em dashes in authored Markdown.

## What this workflow does and does NOT do

- DOES: author/curate a `benchmarks/` suite; capture + diagnose the environment; run the
  benchmarks with warm-up; generate (and, on explicit consent, submit) an HPC job script;
  write a shareable, optionally anonymized results bundle under `workflow-artifacts/`.
- Does NOT: change the product's code, add benchmarking into the product's runtime, modify
  system configuration, auto-submit HPC jobs without per-submission consent, or send
  results anywhere over the network.

## The deterministic helper

`benchmark/tools/bench_env.py` (stdlib-only, read-only w.r.t. system state) does the
mechanical, must-be-reliable parts. Run it by path. Key flags:

- `--repo PATH` inspect this repo/working dir (default `.`).
- `--paths P[,P...]` also inspect data/scratch dirs (to detect NFS working sets, free space).
- `--disk-probe [--probe-mb N]` bounded write/read probe in the OS temp dir (writes only there).
- `--warm P[,P...]` read the given paths into cache before timing (mitigates first-touch/NFS cost).
- `--scrub` redact hostname/user/paths for a shareable report (keeps fs types, sizes, timings).
- `--format json|csv|text`, `--out FILE`, `--version`.

It captures hostname/OS/kernel/arch/python, CPU (model, logical/physical, governor, max MHz,
NUMA, SIMD flags), RAM (total/free/available/cached/used) + swap, load, GPU(s) via
nvidia-smi/rocm-smi, the filesystem type + free space of each path, container/VM hints, and
HPC scheduler presence. It then flags conditions (network-FS working set, powersave
governor, swapping, busy host, login-node HPC use, virtualization) with suggested remedies.

## Step 0: Discover the repo

1. Read the project's intent, stack, and entry points (what a user actually runs: a CLI,
   a library API, a data pipeline, a service). Identify the **hot paths** worth timing.
2. Discover existing benchmarking, if any: a `benchmarks/`/`bench/`/`perf/` dir,
   `pytest-benchmark`, `asv` (airspeed velocity), `hyperfine`, `google-benchmark`, JMH,
   criterion, `go test -bench`, `timeit` scripts. Do not duplicate; extend what exists.
3. Discover the plan/lifecycle and contributor conventions (as other workflows do).
4. Run `bench_env.py --repo . --paths <any data dirs>` once to see the environment and
   whether an HPC scheduler is present. This informs the rest of the wizard.
5. Produce a short **conformance report**: does a benchmark suite exist? is it isolated?
   does it capture the environment? does it warm up? is it HPC-aware? Classify each as
   conformant / partial / missing / not-applicable, and only propose the gaps.

## The steps (go through each; ask before applying)

### 1. Establish the isolated suite

If no isolated suite exists, propose creating `benchmarks/` with:
- a `README.md` telling ANY user how to run it from a clean clone (prerequisites, one
  command, expected runtime, where results land, how to share them);
- a small runner that (a) calls `bench_env.py` first to capture context, (b) runs each
  benchmark case, (c) writes results next to the environment capture;
- one or more **benchmark cases** targeting the hot paths from Step 0, each timing the
  product **out of process** where practical (invoke the CLI / spawn the entry point)
  rather than importing and instrumenting it, to keep the product inert.
Use the project's own language/tooling (pytest-benchmark for Python projects, hyperfine
for CLIs, the language's native bench harness) rather than inventing one. Keep it minimal.

### 2. Wire in environment capture (requirement 1, 6)

Ensure the suite captures the environment BEFORE running, via `bench_env.py --format json
--out <results-dir>/environment.json` (plus `--paths` for data dirs). Every result set
must carry its environment.json so a reader knows the machine, storage, and load it was
measured on. Never report a number without its context.

### 3. Configuration diagnosis and remedies (requirement 2)

Run `bench_env.py` and surface its diagnostics to the user. For each flagged condition
(e.g. "working set is on NFS", "governor is powersave", "host is busy", "on an HPC login
node"), present the suggested remedy. Offer to record the remedies in the suite README so
future runners see them. Do NOT apply system changes yourself; they are the user's to run.

### 4. Warm-up and stable timing (requirement 5, 5a)

Ensure each benchmark runs **at least two full iterations** and reports per-iteration
timings (so the first, cache-cold iteration can be seen and, by default, discarded from
the summary statistic). Before timing, use `bench_env.py --warm <input paths>` (and/or a
first untimed iteration) to absorb file-system caching, NFS automount/fetch, and JIT/import
startup. For NFS/remote working sets, prefer copying inputs to node-local scratch first
(the remedy the diagnostics suggest) over trying to force a mount. Record iteration count
and which iterations are included in the reported statistic.

### 5. Run the benchmarks (consent required)

With the user's confirmation, run the suite. Executing repo code is the core hazard, so
confirm before running and keep runs bounded. Capture per-iteration timings, throughput,
and any resource metrics the harness provides. Write everything to the run record (below).
If the user declines, stop after producing the suite and the environment capture.

### 6. HPC: detect, generate, and (on explicit consent) submit (requirement 3a)

If `bench_env.py` reports a scheduler (Slurm/PBS/SGE/LSF):
- Explain that benchmarking on a login node is unreliable and that a compute-node run is
  better. Offer to **generate a submission script** into `benchmarks/` (e.g. an `sbatch`
  script requesting an exclusive node, a sensible time limit, and the partition from the
  detected partitions hint), wiring it to run the same suite and warm-up.
- Show the generated script. Only if the user explicitly approves THIS submission, run the
  submit command (`sbatch <script>` / `qsub` / `bsub`). Never submit under a batch flag,
  and never guess partitions/accounts/credentials - ask or leave placeholders.
- If no scheduler is present, say so and run locally.

### 7. (Optional) baseline comparison - opt in only

If the user wants a guardrail, offer to save the current summary as a committed baseline
(`benchmarks/baselines/<name>.json`) and to compare future runs against it with an explicit
tolerance band (e.g. warn if slower by more than N%). Keep it OUT of CI unless the user
asks; report drift as information, not a hard failure, because environment variance alone
can exceed typical tolerances. This is the only place benchmarking touches regression, and
only on request.

### 8. Produce the shareable results bundle (requirement 3)

Write the run record and offer to prepare a shareable bundle (Step "Run record" below),
optionally anonymized with `--scrub`. Tell the user exactly how to share it (attach the
bundle to an issue or PR, or send it), and what it contains, so they can review before
sharing. The tool makes no network calls; sharing is always the user's explicit action.

## Run record

Create `workflow-artifacts/benchmark/<RUN_ID>/` (RUN_ID = UTC `YYYYMMDD-HHMMSS`), a
committed deliverable. Write:

- `environment.json` - the full `bench_env.py --format json` capture (the context).
- `results.json` - per-benchmark, per-iteration timings/throughput/metrics, the iteration
  count, which iterations are included in the summary statistic, and the exact commands run.
- `report.md` - a human summary: the machine (from environment.json), the diagnostics and
  their remedies, the results with variance, warm-up handling, any HPC submission, and how
  to reproduce and share. Lead with a one-line honesty note if any relevant condition was
  flagged (e.g. "measured on an NFS working set; treat I/O numbers as indicative").
- optionally a scrubbed copy for sharing (`report.scrubbed.md` / `environment.scrubbed.json`).

Do not git-ignore `workflow-artifacts/`. Keep the record local only if the user asks.

## Required report format (to the user)

```
## Benchmark - <repo/scope>
Suite: <path to benchmarks/ or "existing: <tool>">   Isolated: <yes/no + why>
Environment: <host summary; flagged conditions count>
Ran: <yes/no; iterations; local or HPC(<scheduler>)>
Run record: <workflow-artifacts/benchmark/<RUN_ID>/>

### Environment diagnostics
| Severity | Area | Finding | Suggested remedy |
|----------|------|---------|------------------|

### Results (with variance; first/cold iteration handling noted)
| Benchmark | Iterations | Metric | Value | Spread |
|-----------|------------|--------|-------|--------|

### Notes and caveats
- <honesty notes: what could skew these numbers; what was not measured>

Next step: <review the suite / run it / submit to HPC / share the bundle>. This workflow
does not change product code and does not publish results.
```

Be rigorous and honest. Report variance, not just a best-case number. State plainly what
the environment could distort and what was not measured. Never present a benchmark result
without the environment it was measured in.
