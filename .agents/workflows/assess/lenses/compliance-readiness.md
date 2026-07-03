# Lens: Compliance readiness (FIPS / NIST 800-171 / CMMC L2 and similar)

Focus the assessment on **readiness** for a formal compliance regime - by assessing
only the slice of its controls that is visible and verifiable in this repository, and
explicitly enumerating the (usually larger) slice that is organizational and cannot be
assessed from code. Parameterized by regime via `$ARGUMENTS` (e.g.
`fips`, `nist-800-171`, `cmmc-l2`); if none is given, ask which regime(s) apply.

## Critical honesty constraints (read first - these are not optional)

These regimes are **mostly organizational and operational**, not code. For NIST
800-171 (110 controls across 14 families) and CMMC Level 2 (which maps to them), the
large majority of requirements concern policies, procedures, training, physical
security, personnel, incident-response *processes*, configuration-management
*procedures*, and audited organizational behavior - **none of which live in a
repository**. A repo agent can assess only the thin technical slice.

Therefore this lens MUST:

1. **State plainly, in the IPD, that it is NOT a certification, NOT an audit, and NOT
   a substitute for a qualified assessor** (e.g. a C3PAO for CMMC) or legal/compliance
   counsel. It assesses *technical readiness signals visible in the repository only*.
2. **Classify every control it considers** as one of: `repo-verifiable`,
   `repo-partial`, `org-level-out-of-scope-of-repo`, or `not-applicable` - with
   evidence for the first two and a clear statement that the org-level ones require
   separate, non-repo evidence.
3. **Never report an overall "compliant"/"ready" verdict for the regime.** Report only
   the repo-slice posture and the explicit gap list. Overstating coverage in a federal/
   CUI context is harmful; err toward under-claiming.
4. **Recommend a qualified human assessment** for the full regime.

## Lead personas

Stakeholder (regulatory/contractual exposure, who owns the org-level controls) and the
security-minded architect, with the relevant concern persona per control (privacy,
logging-audit, security, access control).

## Per-regime control catalogues (repo-relevant slice)

Enumerate the regime's controls; below are the parts most often repo-verifiable. For
each, gather evidence and classify per the constraints above.

### FIPS (FIPS 140-2/140-3 validated cryptography; FIPS 199/200 context)

- Cryptographic modules in use are **FIPS-validated** (not just "uses AES") - identify
  the crypto libraries and whether a validated module / FIPS mode is used.
- Approved algorithms and key sizes only (no MD5/SHA-1 for security, no DES/RC4, RSA/EC
  key sizes within policy); approved RNG/DRBG; no homegrown crypto.
- TLS configuration restricted to approved versions/ciphers; FIPS mode enforced where
  the platform supports it.
- Key management: generation, storage, rotation, destruction handled with approved
  mechanisms (cross-reference security).

### NIST SP 800-171 (protecting CUI; 14 families)

Repo-verifiable or partial slices, by family:

- **Access Control (3.1):** authZ enforced in code, least privilege, session
  lock/timeout, separation of duties hooks, remote-access controls in code.
- **Audit & Accountability (3.3):** security event logging, content, timestamps,
  tamper protection, retention (cross-reference logging-audit).
- **Configuration Management (3.4):** secure baselines/IaC, least-functionality,
  no insecure defaults, dependency control (cross-reference supply-chain).
- **Identification & Authentication (3.5):** unique IDs, authenticator management,
  MFA hooks, no hardcoded/replayable credentials.
- **System & Communications Protection (3.13):** encryption in transit/at rest, FIPS
  crypto, boundary protection in code, key management.
- **System & Information Integrity (3.14):** input validation, flaw remediation
  (dependency patching), integrity verification, error handling.
- Mostly **org-level (mark out-of-scope-of-repo):** Awareness & Training (3.2),
  Incident Response (3.6), Maintenance (3.7), Media Protection (3.8), Personnel
  Security (3.9), Physical Protection (3.10), Risk Assessment (3.11), Security
  Assessment (3.12) - assess these as process/evidence the repo cannot supply.

### CMMC Level 2

CMMC L2 practices map to the NIST 800-171 controls above; apply the same repo-slice
analysis and the same family split. Additionally note that CMMC requires an SSP, POA&M,
and (for many) a third-party (C3PAO) assessment - all org-level and out of repo scope.

### Other regimes

If asked for another regime (e.g. FedRAMP technical controls, 800-53 subsets), apply
the same method: enumerate, classify repo-verifiable vs org-level, evidence the
technical slice, and route the rest to humans.

## IPD emphasis

Produce a control-by-control readiness table (control | classification | evidence |
gap | proposed repo fix or "org-level: needs non-repo evidence"). Propose concrete,
repo-level fixes for the technical slice (enable FIPS mode, replace a non-approved
algorithm, add audit logging fields, enforce session timeout, encrypt a data store,
remove a hardcoded credential) - most are low Remediation Risk and should be proposed
by default. Clearly separate "the repo can fix this" from "this needs an organizational
control / policy / assessor evidence", and put the latter in a dedicated section the
human owner must act on. Restate the not-a-certification framing in the IPD's verdict.
