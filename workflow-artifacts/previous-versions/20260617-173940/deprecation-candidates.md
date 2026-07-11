# Deprecation Candidates - 20260617-173940

The following items are identified as potential candidates for deprecation or removal.

## CLI Options

### 20260617-173940-S1-DEP1: `--use-model` / `-m` CLI Argument
- **Status**: Deprecated in favor of `--compact`
- **Location**: [ocman.py](file:///home/gfariello/VC/ocman/ocman.py#L3687)
- **Evidence**: The argument is suppressed in `--help` (`help=argparse.SUPPRESS`) and bridged to `args.compact` at line 4457.
- **Recommendation**: Safe to keep as deprecated/suppressed for backward compatibility, but can be scheduled for future removal once downstream scripts migrate to `--compact`.

## Scripts

### 20260617-173940-S1-DEP2: `rebuild_opencode.sh`
- **Status**: Obsolete
- **Location**: [rebuild_opencode.sh](file:///home/gfariello/VC/ocman/rebuild_opencode.sh)
- **Evidence**: The script performs a complete dump-and-rebuild, which was proven ineffective at solving database bloat (since the bloat was due to live `event` rows, not internal fragmentation). `ocman.py` now provides the proper session-rooted pruning and `VACUUM`.
- **Recommendation**: Keep for debugging/emergency dump-rebuilds, or mark deprecated and suggest using `ocman --clean` instead.
