# Guiding-principles adherence (run 20260707-004045)

Principles source: `ARCHITECTURE.md` "Design principles" + universal fallback (no dedicated
GUIDING_PRINCIPLES.md). Per-principle verdict finalized in Section 5/8; seeded here.

- Intuitive / self-documenting: (assess in S4/S5)
- Configurable over hardcoded: (assess in S5)
- KISS: (assess in S5)
- Honest documentation: (assess in S4)

## Update (S4)
- Honest documentation: HELD. README config keys == DEFAULT_CONFIG (0 undocumented); --help matches
  the shipped filter/--allow-secrets surface; CHANGELOG honestly flags the --compact behavior change.
- Intuitive/self-documenting (docs side): HELD, minus D1 (migration-script discoverability, Low).

## Final per-principle verdict (S5)
- Intuitive / self-documenting: HELD with two Low nits (S4-D1 migration discoverability, S5-U1
  --force help). Both fixed in S7.
- Configurable over hardcoded: HELD - filter_max_bytes / filter_secret_scan are config keys with
  CLI overrides; TUI now honors default_out_dir (removed a hardcoded path).
- KISS: HELD - egress + collision logic are single shared helpers reusing existing primitives; no
  speculative abstraction. The delta is proportionate.
- Honest documentation: HELD - docs match behavior; CHANGELOG flags the --compact behavior change.
