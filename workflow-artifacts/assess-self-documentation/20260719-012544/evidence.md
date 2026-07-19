# Evidence - assess self-documentation

## Inspected (CLI, `ocman/cli.py`)

- Error/`die`/`RecoveryError` sites: 544-547, 826-850, 930-933, 970-990, 1084 (RecoveryError),
  1198 (die), 1275-1277, 4935-4941 (DurationError), 5320, 7406, 7503-7526, 7816-7819,
  8057-8087, 8286, 8336-8339, 8612, 8842-8844, 9283, 10213-10551 (bundle import),
  15851-15853.
- Help system: HELP_TOPICS 5447-5455; build_help 5504+; build_help_reference 5635+;
  print_help 5737; `_OcmanHelpAction` 6010-6024; per-command `-h` 6045-6046; overview
  tiers/aliases 5605-5716; unknown-topic message 6919-6921.
- Parser / flags: build_parser and `new_sub`/`new_action` 6173-6478; `_add_extract_opts`
  6129-6134; `_add_clean_opts` duration/`--older-than` 6146-6151; reclaim flags 6455-6474;
  doctor flags 6448-6453; SUPPRESSed flags 6105-6106, 6151, 6383, 6399; recovery short flags
  6059-6083.
- First-run / onboarding: no-args normalize 6636-6639; `print_no_project_context_help`
  4841-4865; usage line note 5614; `ocman config create` 12459-12520; `doctor` output
  14231-14316 (suggested order 14290-14292, buckets 14283-14285).
- Top-level exception handling in main(): 16309-16313.
- Direct re-verification: `grep -n "--show-models|--list-projects"` (stale in error strings at
  828, 7525; NOT registered as args); `die` signature 1198; DurationError raise sites
  4935/4939/4941.

## Inspected (TUI, `ocman_tui/`)

- Empty states: sidebar.py:39,66; spend.py:65; running.py:71-78; database.py:116;
  app.py:1073,1098,1493,1538,1132-1134.
- Placeholders / worked examples: app.py:111,671,722,724,815,874,878,1061,1174-1184;
  database.py:241,246; models.py:21.
- Destructive-action labeling: app.py:1123-1136 (DANGER ZONE), typed-"yes" placeholders
  140,182,236,364; storage.py:48-59,75-106,229-265 (reclaim previews + CLI-only note);
  read-only/observe-only tab titles storage.py:75,87, spend.py:23, running.py:24.
- Footer key bindings: app.py:1026-1030,1191.

## Commands run

- `ls .agents/workflows/assess/lenses/` to resolve the concern.
- `grep -n` for stale flags, `die`/RecoveryError signatures, duration error sites.
- Reads of the files/line ranges above (via a thorough explore pass, then direct
  re-verification of SD-01 and SD-02).

## Sampling / truncation notes

- `ocman/cli.py` is ~16.3k lines; the help system, parser, error sites, onboarding path, and
  the named line ranges were read; the file was not read end-to-end.
- No DB or runtime execution was needed (static, in-product-text assessment).
