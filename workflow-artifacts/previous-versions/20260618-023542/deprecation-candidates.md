# Deprecated and Obsolete Candidates

This file records deprecated, obsolete, stale, or unused code and artifacts identified during the repository review.

| Candidate ID | Target Item | Classification | Description / Evidence | Recommended Action |
|---|---|---|---|---|
| `20260618-023542-DEP1` | `rebuild_opencode.sh` | Safe to remove now | The script contains a header warning declaring it deprecated and obsolete, recommending `ocman --clean` instead. Its functional capability is completely covered by `ocman`. | Remove the file `rebuild_opencode.sh`. |
