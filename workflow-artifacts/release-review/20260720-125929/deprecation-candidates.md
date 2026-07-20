# Deprecation Candidates


## Section 5

- The `fail-fast: false` override + its explanatory comment in `.github/workflows/ci.yml` is a
  TEMPORARY diagnostic artifact that should be removed (restored to default) now that the matrix
  is green. Classified: safe to remove now. Tracked as finding S1-CI1 (fixed in Section 7).
- No other deprecated/obsolete/stale candidates surfaced in the delta.
