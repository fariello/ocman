# Deprecation Candidates

- **Run ID**: 20260617-193252

This document registers code, files, or scripts in the repository that are deprecated, obsolete, stale, or unused, along with the safety risk and action recommendations.

## Discovered Candidates

### 20260617-193252-S1-DEP1: `rebuild_opencode.sh`
- **File Path**: [rebuild_opencode.sh](file:///home/gfariello/VC/ocman/rebuild_opencode.sh)
- **Status**: Obsolete & Deprecated
- **Classification**: Candidate for future removal
- **Evidence/Rationale**: The script comments state: `WARNING: This script is DEPRECATED and OBSOLETE. It performs a complete dump-and-rebuild, which is ineffective at solving database bloat. Use the official 'ocman --clean' utility instead.`
- **Action/Risk Assessment**: Since `ocman --clean` and TUI prunes are fully implemented and verified, this script is no longer needed. However, since it is a script exposed at the repository root, removing it now should be reviewed. It's safe to keep it marked deprecated, or remove it if confirmed unused by other automation scripts. We will recommend its deletion.

### 20260617-193252-S1-DEP2: `SPEC-orsession.md`
- **File Path**: [SPEC-orsession.md](file:///home/gfariello/VC/ocman/SPEC-orsession.md)
- **Status**: Superseded
- **Classification**: Safe to remove now
- **Evidence/Rationale**: This contains the detailed specification of the legacy standalone `orsession` application, which has been completely retired and deleted in this branch. The new unified specification is at `agents/plans/ocman_gui_spec.md`.
- **Action/Risk Assessment**: Safe to delete, as it is obsolete documentation.

### 20260617-193252-S1-DEP3: `opencode_db_cleanup_handoff_for_claude.md`
- **File Path**: [opencode_db_cleanup_handoff_for_claude.md](file:///home/gfariello/VC/ocman/opencode_db_cleanup_handoff_for_claude.md)
- **Status**: Stale handoff document
- **Classification**: Safe to remove now
- **Evidence/Rationale**: This was a task handoff document created for a previous agent/run, which has since been completed.
- **Action/Risk Assessment**: Safe to delete as it is a temporary documentation artifact.
