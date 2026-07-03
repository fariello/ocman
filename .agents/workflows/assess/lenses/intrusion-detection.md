# Lens: Intrusion detection readiness

Focus the assessment on whether the system *generates the signals* needed to detect
intrusion and abuse, and whether those signals are trustworthy and reach somewhere
they can be acted on. This is repo-scoped: the agent assesses what the code emits and
how it is structured for detection - it does not run a SIEM/IDS or watch live traffic.

## Lead personas

The security-minded architect and operator (detection/response), with the software
engineer on the logging/event code paths.

## Rubric

- **Security-relevant events emitted:** are these logged with enough context to detect
  an intrusion - authentication (success/failure, lockouts), authorization denials,
  privilege changes, admin/sensitive actions, account/credential changes, config
  changes, data access/export, input-validation rejections, and unexpected errors?
- **Event quality:** structured, parseable events with who/what/when/where/outcome, a
  correlation/trace ID propagated across services, stable event types, and accurate
  timestamps (synced, timezone-correct). Avoid logs that are unparseable or missing
  the actor/resource.
- **Tamper-evidence & integrity:** can an attacker erase or forge their tracks? Audit
  logs append-only / write-once / shipped off-box; integrity protection where it
  matters (cross-reference logging-audit and ransomware-resilience).
- **Detectability of known attack patterns:** would brute force, credential stuffing,
  enumeration, injection attempts, abnormal data egress (cross-reference
  data-exfiltration), or privilege escalation produce a visible, distinguishable
  signal?
- **Alerting hooks:** does the system expose metrics/events to an external monitoring
  or alerting system, or are signals trapped in local logs no one watches? Health and
  anomaly surfaces.
- **Noise & signal:** is logging so noisy that real signals drown, or so sparse that
  attacks are invisible? Rate-limit/sample without dropping security events.
- **Secrets in detection data:** events must not themselves leak secrets/PII
  (cross-reference data-exfiltration).
- **Coverage gaps:** code paths that perform sensitive actions with no audit trail.

## IPD emphasis

Propose adding/standardizing security event logging for the high-value events first
(authN/Z, privilege, sensitive data access, config change), with structured fields and
a correlation ID, and a path to ship them off-box. Most logging additions are low
Remediation Risk - propose by default. Be explicit that detection also needs
*operational* components (a SIEM, alert rules, on-call) that live outside the repo;
route those to the operator. This lens assesses detection *readiness in the code*, not
a deployed detection capability.
