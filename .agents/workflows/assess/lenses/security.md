# Lens: Security

Focus the assessment on security posture: protecting the system and its data from
misuse, compromise, and abuse.

## Lead personas

The security-minded architect and software engineer, with the stakeholder view on
breach/compliance/reputational risk.

## Rubric

- **Threat model:** who are the attackers, what are the assets and trust boundaries?
  Reason about realistic abuse, not just the happy path.
- **Authentication:** no trust of unverified input for identity; no defaulting to a
  privileged user; session/token handling; MFA where warranted; mocks gated to
  non-production.
- **Authorization:** default-deny; route-level AND object/row-level checks; tenancy
  scoping so no request crosses tenants; reconsider blanket admin bypasses.
- **Input handling:** validation at boundaries (reject unknown fields); injection
  (SQL/command/template/path/XSS/SSRF/deserialization); upload type/size/scan
  hardening.
- **Secrets:** none hardcoded; via a manager; fail-fast if absent in prod; no secrets
  in logs, errors, or client payloads.
- **Crypto & transport:** TLS everywhere; vetted algorithms; correct randomness; safe
  password storage; no homegrown crypto.
- **Dependencies / supply chain:** known-vulnerable or abandoned packages, integrity
  pinning (coordinate with the supply-chain lens if both apply).
- **Error handling & disclosure:** safe error envelopes; no stack traces/internals to
  clients; rate limiting and lockout that work across a stateless fleet.
- **Logging/audit:** security-relevant events are logged without leaking secrets;
  tamper-evidence where needed.

## IPD emphasis

Prioritize Blocker-class exposures (data loss/breach, auth bypass, injection). When
proposing fixes, prefer defense in depth and fail-safe defaults; do not propose
changes that weaken posture for convenience. Flag anything needing a human security
decision as an open question rather than guessing.
