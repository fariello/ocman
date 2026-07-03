# The Fix Bar (decision policy for what to address)

This is the canonical decision policy for what the release review fixes. It is
referenced by `00-run-protocol.md` and applied during Section 7 implementation. It
overrides any older "favor high-priority only" or "minimize changes" framing.

---

**Core principle: fix by default. Deferral is the exception that must be justified.**

The executing agent is fast, cheap, and efficient, so the time, effort, or token
cost of a fix is NOT a reason to skip it. Flip the usual question. Do not ask "is
this important enough to fix?" Ask: "is there a strong enough reason NOT to fix
this?"

## The decision rule

> FIX the finding unless the *Remediation Risk* of fixing it is Medium-High or
> higher. When unsure whether it reaches that bar, prefer to fix and note the
> uncertainty (fail-safe).

This means everything gets addressed by default: small bugs, nits,
wording/polish, missing-but-required capabilities, usability and self-documenting
gaps, guiding-principles violations, and over-scoped/gold-plated features (for
those, the "fix" is to recommend removing or deferring them).

## "Remediation Risk" - the only thing that justifies NOT fixing

Remediation Risk is the risk that *applying the fix itself* harms one or more of
these axes, now or in the future:

- **Complexity** - the fix adds disproportionate architectural complexity or
  maintenance burden (a real "keep it simple" cost). This is the main
  counterweight: do not let "it is cheap to add" become an excuse for gold-plating
  or over-engineering. Unjustified complexity is a valid reason to defer.
- **Usability** - the fix degrades the user experience or makes things less
  intuitive.
- **Security** - the fix opens, weakens, or complicates the security posture.
- **Functionality** - the fix risks breaking current or planned/future behavior.

Rate it Low / Medium / Medium-High / High:

- **Low or Medium: FIX NOW.**
- **Medium-High or High: DEFER**, but only with an explicit, recorded
  justification naming which axis and why. Where possible, do the safe part now
  and defer only the risky remainder. Never silently drop a finding.

Explicitly excluded from Remediation Risk: effort, time, and token/compute cost.
The only question is whether the change makes the system more complex, less usable,
less secure, or less correct.

## Severity is for reporting, not for deciding

Findings are still labeled by impact if left alone (Blocker / High / Medium /
Low), but severity does not decide whether to fix; the Remediation-Risk gate does.
A "Low/cosmetic" finding still gets fixed by default; a "High" finding is only
deferred if its *cure* clears the Medium-High risk bar.

The `LIVE`/High data-integrity non-deferral rule (Sections 2 and 7) still applies:
those findings must be fixed in-run or explicitly escalated to the user,
regardless of the Fix Bar.

## Scope is checked separately (two directions)

- **Over-scope:** a feature, abstraction, or dependency not traceable to a stated
  requirement or the project's purpose. Flag it; default action is remove/defer
  (usually low Remediation Risk, so do it).
- **Under-scope:** a required capability that is missing. Add it by default.

## Practical caveat

This bar makes "do everything" the default, so the active discipline becomes
guarding against scope creep. The Complexity axis is what keeps a cheap-to-add fix
from quietly violating "keep it simple"; that is the one judgment to exercise most
carefully.
