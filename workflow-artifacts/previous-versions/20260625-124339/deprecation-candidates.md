# Deprecation and Obsolete Candidates

- **Run ID**: `20260625-124339`

| Candidate ID | Target | Description | Classification | Rationale |
|---|---|---|---|---|
| `20260625-124339-S1-DEP1` | `opencode.json` / `opencode.jsonc` (root) | Local debug/test configurations | Safe to exclude/remove from package | These are local config templates/tests and should not be distributed in the final Python package. (Hatch package build filters should ignore them). |
