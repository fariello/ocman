# Deprecation Candidates

| ID | Candidate | Evidence | Classification | Notes |
|---|---|---|---|---|
| DEP1 | `orsession/` package | Imported optionally by ocman.py (`from orsession.core import expand_config_refs`); superseded by `ocman_tui`; historic name "orsession" | Probably still needed (soft dependency) | Not shipped in wheel (only ocman_tui + ocman.py). Verify import still resolves; low risk. Do not remove this run. |
| DEP2 | "Orsession" naming residue (class `OrsessionApp`, docstrings) | Project renamed to ocman but TUI class/app title still "Orsession" | Safe to mark for future rename | Cosmetic; renaming public class is Medium risk (functionality/imports). Defer. |
| DEP3 | `agents/`, `prompts/` dirs | Present at repo root, not in wheel packaging | Unknown — requires human review | Not obviously part of shipped product; leave tracked. |
| DEP4 | `__pycache__/` at repo root (tracked?) | Present in `ls` | Check if tracked | If tracked, should be gitignored (it is in .gitignore). No action unless tracked. |

No code marked deprecated this run without strong evidence.
