# Implementation Plan 04 - compact secret visibility/expunge & -y/--yes

Status: PROPOSED (not yet executed)

IPD 04 in the execution order (independent of 01-03, though it shares the
`-y/--yes` definition with 03). Adds, to `session compact` (and the shared
egress guard used by `filter`), the ability to see what secrets/PII were
detected and to expunge them from what is sent (and optionally from saved
recovery files), plus a `-y/--yes` to skip the cost/egress confirmation.

---

## Motivation

The egress guard (`check_egress_guards` -> `scan_for_secrets`,
`ocman.py:6023-6072`) currently refuses on detection and prints only redacted
`type@line` summaries, never the value. Users want to (1) inspect what was
flagged, and (2) strip it and proceed, without hand-editing transcripts. They
also want a `-y` to skip the interactive cost/egress confirmation for scripts.

---

## User Review Required

> [!IMPORTANT]
> - Default posture stays "never echo secrets". `--show-secrets` shows the
>   matching LINES with the secret MASKED (context, not the raw value).
> - An explicit, friction-ful escape hatch allows UNREDACTED viewing:
>   `--show-secrets=raw` (and an interactive "reveal (r)" choice), which prints a
>   clear warning about scrollback/log exposure before echoing values. It is
>   never the default and never implied by `--expunge-secrets`.
> - `--expunge-secrets` redacts detections in the OUTBOUND copy sent to the LLM
>   (the DB is never mutated). It ALSO offers to redact the saved
>   recovery/restart/compacted files written to disk. It never scrubs the
>   opencode DB.
> - `-y/--yes` skips the cost/egress confirmation (and the delete confirm in
>   IPD 03). It does NOT bypass the secret guard, ambiguity resolution, or the
>   process-lock (`--force`).

---

## Design

### Detection model changes

`scan_for_secrets` returns `SecretHit(kind, line)` only (`ocman.py:5989-6037`).
Extend the hit to also carry the match span so masking/redaction is possible
WITHOUT changing the default output:

- Add `col_start`/`col_end` (span within its line) to `SecretHit`. `scan_for_
  secrets` currently uses `pat.search(line)` and records one hit per (pattern,
  line) (`ocman.py:6031-6036`); switch to `pat.finditer(line)` so EVERY match on
  a line gets a span. The span value is NEVER printed unless the user opts into
  raw viewing.
- **Overlapping detectors.** Multiple patterns (e.g. `credential-assignment` and
  the aggressive `keyword`) can match the same or overlapping spans on one line.
  `redact_secrets` MUST merge overlapping/adjacent spans per line before
  replacing, so a region is redacted once (no double-substitution, no partial
  leftover). Redact right-to-left within a line to keep earlier offsets valid.
- Add a `redact_secrets(text, hits) -> str` pure function that replaces each
  merged span with a fixed placeholder (e.g. `<REDACTED:kind>`), preserving line
  structure and count. Unit-testable, no I/O. Property: re-scanning the output
  yields no hits.
- Add a `mask_line(line, hit) -> str` helper that returns the line with only the
  secret span(s) masked (e.g. `api_key=**********`) for `--show-secrets` context.

### Compact / egress flags

On `session compact` (and, where it makes sense, `filter`):

- `--show-secrets[=masked|raw]` (default when present: `masked`). `masked`
  prints each detection's line with the value masked. `raw` prints the actual
  matched value after a prominent warning; on a TTY it additionally requires a
  typed confirm ("type 'reveal' to show secret values"). Interactive review of a
  blocked send offers `[s]how masked / [r]eveal raw / [e]xpunge / [a]bort`.
- `--expunge-secrets`: build a redacted outbound copy via `redact_secrets` and
  compact THAT. Then, if recovery/compacted files were written, offer (prompt;
  or auto with `-y`) to rewrite those on-disk files through `redact_secrets`
  too. Print a summary of how many detections were redacted (by kind), never the
  values.
- Interaction with `--allow-secrets` (`ocman.py:5233`): `--allow-secrets` sends
  as-is (unchanged). `--expunge-secrets` sends a redacted copy. They are mutually
  exclusive; specifying both is an error.
- `check_egress_guards` gains an optional expunge path: when expunging, it
  redacts and returns the cleaned text instead of raising; when not, behavior is
  unchanged (raise on detection unless `--allow-secrets`).

### `-y/--yes`

Add `-y/--yes` to `compact`. It skips the interactive "Proceed with compaction?"
prompt (`ocman.py:5943-5947`) and the batch cost confirm (IPD 03). It does not
bypass the secret guard: if secrets are detected and neither `--allow-secrets`
nor `--expunge-secrets` is set, the run still refuses (a `-y` script must choose
one explicitly). Shared definition with IPD 03.

### Safety

- Raw reveal is gated behind an explicit value (`=raw`) plus a TTY typed confirm;
  never triggered by `-y` or by `--expunge-secrets`.
- Redaction operates only on copies (outbound text and, opt-in, output files);
  the opencode DB and original transcripts are untouched.
- No secret value is ever written to logs, history, or error text.

---

## Tests

- `redact_secrets` replaces each pattern with a placeholder and preserves line
  count; round-trips through the scanner (no hits after redaction).
- overlapping detections on one line (credential-assignment + keyword) are
  merged and redacted once, with no leftover secret substring and no corruption
  of surrounding text; a line with two DISTINCT secrets redacts both.
- `--show-secrets` (masked) prints context with the value masked; asserts the
  raw value is absent from output.
- `--show-secrets=raw` requires the typed confirm on a TTY; without it, values
  are not printed.
- `--expunge-secrets` sends a redacted payload (assert the API-bound text has no
  hits) and offers to scrub output files; DB untouched.
- `--allow-secrets` + `--expunge-secrets` together is an error.
- `-y` skips the proceed prompt but a detected secret with no allow/expunge
  still refuses.

---

## Docs

- README + help: `--show-secrets[=masked|raw]`, `--expunge-secrets`, `-y/--yes`,
  and the explicit note that raw reveal is a deliberate, warned opt-in.
- ARCHITECTURE / CONVENTIONS: document that ocman still never logs secret values
  and redaction never touches the DB.

---

## Non-goals

- Scrubbing secrets from the opencode DB (explicitly out of scope; decided).
- New detector patterns beyond the current set (separate concern).
