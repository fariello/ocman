# Decisions - 20260617-173940

## Decisions and Judgments

### 20260617-173940-DEC1: Serial Audit Mode
- **Decision**: Perform all audits (Sections 1-6) serially rather than using parallel audit lanes.
- **Rationale**: The repository is relatively compact (primarily a single CLI file `ocman.py` and a TUI package with two main files `app.py` and `core.py`). Serial execution by the main agent ensures deep, consistent analysis and keeps findings well-integrated.

### 20260617-173940-DEC2: Scope of Target Code
- **Decision**: Limit target codebase audit to `ocman.py` and the `orsession` package files (`app.py`, `core.py`).
- **Rationale**: `scripts/check_orsession.sh` and `rebuild_opencode.sh` are minor ancillary scripts and don't affect runtime core features.
