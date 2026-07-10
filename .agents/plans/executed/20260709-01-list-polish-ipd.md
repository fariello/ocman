# Implementation Plan 01 - list polish: `list models` & session stats columns

Status: EXECUTED

Small consistency/UX improvements. Provides `resolve_model_spec` used by IPD 02
(batch target resolver). This is IPD 01 in the execution order.

---

## Motivation

- `ocman models` is inconsistent with the noun-based grammar; `ocman list models`
  reads like `list projects` / `list sessions`.
- `list sessions` would be more useful with an approximate interaction/message
  count per session.

---

## User Review Required

> [!IMPORTANT]
> - `ocman list models` becomes the primary form; keep `ocman models` as an
>   alias so nothing breaks.
> - `list sessions` adds APPROXIMATE per-session counts from cheap DB aggregates
>   (one grouped query over all listed sessions), shown by default and labeled
>   approximate. True transcript "line" counts require exporting each session and
>   are NOT computed here (would be slow); the column shows message/part-derived
>   proxies, honestly labeled, not a claim of transcript lines.

---

## Design

### `list models`

- Add `models` to the `list` word-order branch in `preprocess_argv`
  (`ocman.py:4885-4890`). Note that branch rewrites `list projects` ->
  `["project","list", ...]` (a group+action), but `models` is a TOP-LEVEL
  subcommand (`new_sub("models")`, `ocman.py:5370`), not `model list`. So the
  rewrite for `list models` MUST be `["models", *rest[2:]]` (a single token),
  NOT `["model","list"]`. Keep the bare `ocman models` working (it already is).
- Add a test asserting `preprocess_argv(["ocman","list","models"]) ==
  ["ocman","models"]`.
- Update the help renderer rows (`build_help`/`build_help_reference`) to show
  `list models`.

### `resolve_model_spec` (shared with IPD 02)

- Add `resolve_model_spec(spec, models) -> ModelInfo | None | "ambiguous"`
  mirroring `resolve_session_spec`: exact `provider/model_id`, exact `name`,
  else unique case-insensitive substring over
  `extract_models_from_config(...)` (`ocman.py:585`). Multiple substring matches
  -> ambiguous; used by IPD 02's batch resolver and by `compact`'s model pick.

### `list sessions` approximate stats

- Add a single grouped aggregate (e.g. `SELECT session_id, COUNT(*) FROM message
  GROUP BY session_id`, and similarly for `part`) computed once for the whole
  listing, joined in memory to the session rows already produced by
  `db_list_sessions` / `db_list_sessions_under_dir` (`ocman.py:3869`, `3938`).
  Avoid per-session queries.
- Show two approximate columns, honestly labeled, e.g.
  `~msgs: N  ~interactions: M` where interactions is derived from user-role
  message rows if cheaply distinguishable, else omitted with only `~msgs`. Do
  NOT print a "lines" column implying transcript line counts (not knowable
  cheaply); if a stand-in is shown it is labeled `~parts`.
- Header/legend clarifies these are approximate DB-derived counts.
- Keep the listing fast on large DBs; verify the extra aggregate is a single
  indexed scan (add an informational note if it is not).

---

## Tests

- `ocman list models` runs and matches `ocman models` output.
- `resolve_model_spec`: exact provider/model, exact name, unique substring
  resolve; ambiguous substring returns ambiguous; no match returns None.
- `list sessions` shows the approximate columns; a session with known
  message/part rows reports matching counts; the grouped query is issued once
  (not per session).

---

## Docs

- README + help: `list models`; document the approximate `list sessions`
  columns and that they are DB proxies, not exact transcript metrics.

---

## Non-goals

- Exact interaction/line counts (would require exporting; a `--stats` opt-in was
  considered and deferred).
- Renaming/removing the `ocman models` alias (kept for back-compat).
