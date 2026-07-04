# Deprecation Candidates

Carried forward from run 20260703-134213 (no new candidates from the v1.0.3->HEAD delta).

| ID | Candidate | Classification | Notes |
|---|---|---|---|
| DEP1 | `orsession/` package (optional import) | Probably still needed | Soft dependency; not shipped in wheel. No change. |
| DEP2 | "Orsession" naming residue (`OrsessionApp`, title) | Safe to mark for future rename | Public class rename = Medium functionality risk. Defer. |
| DEP3 | `agents/`, `prompts/` dirs | Unknown — human review | Not in wheel; leave tracked. |

No code deprecated/removed this run.
