# Lens: Logging and audit trail quality

Focus the assessment on the quality, completeness, integrity, and safety of the
system's logging and audit trail. Good logging underpins debugging, operability,
intrusion detection, incident response, and many compliance controls - so this lens is
foundational and frequently cross-referenced.

## Lead personas

Operator and software engineer, with the security-minded view on audit integrity and
the privacy view on what must NOT be logged.

## Rubric

- **Coverage:** are the events that matter logged - errors and exceptions (with
  context, not swallowed), security events (cross-reference intrusion-detection),
  state changes, sensitive/admin actions, integrations, and lifecycle (start/stop/
  config)? Gaps where a failure would leave no trace.
- **Structure & consistency:** structured (machine-parseable) logs with consistent
  fields; a correlation/trace ID propagated across components; consistent levels used
  meaningfully (not everything at INFO or ERROR); stable, queryable event types.
- **Context & actionability:** enough context to diagnose without reproducing
  (who/what/when/where/outcome/identifiers); messages that help rather than "an error
  occurred".
- **Audit trail integrity:** for audit/compliance-relevant records - append-only,
  tamper-evident (hashing/signing/chaining where warranted), serialized writes (no
  read-then-write races), queried by an indexed monotonic key, retained per policy,
  and shipped off-box so local compromise cannot erase them.
- **What must not be logged (privacy/security):** secrets, credentials, tokens, full
  PII, payment data, session identifiers. Redaction/masking at the logging boundary
  (cross-reference data-exfiltration and privacy).
- **Time correctness:** synchronized clocks, unambiguous timezones (prefer UTC), and
  ordering that survives concurrency.
- **Volume, retention, cost:** sensible levels and sampling that do not drop security/
  audit events; rotation/retention; not so noisy that signal is lost nor so sparse that
  incidents are invisible.
- **Failure handling of logging itself:** logging failures do not crash the app or
  silently lose audit records; backpressure handled.

## IPD emphasis

Propose closing coverage gaps for high-value events first, then structure/correlation,
then audit-integrity for compliance/security-relevant records, then redaction of
anything sensitive. Most logging improvements are low Remediation Risk - propose by
default. Note where log *aggregation/retention/SIEM* is an operational concern outside
the repo. This lens assesses the logging the code produces and how it is structured,
not a deployed log pipeline.
