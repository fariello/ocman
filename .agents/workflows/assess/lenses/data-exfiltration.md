# Lens: Data exfiltration resistance

Focus the assessment on how (and how easily) sensitive data could leave the system -
whether by an attacker, a compromised dependency, a misconfiguration, or accidental
over-sharing - and on the controls that detect and limit such egress. This is a
repo-scoped, static assessment of code/config/IaC; it does not observe a live network.

## Lead personas

The security-minded architect and software engineer, with the stakeholder on the
business/regulatory impact of a data loss and the privacy view on what data is at
stake (cross-reference the privacy and security lenses).

## Rubric

- **Sensitive data inventory & sinks:** what sensitive data exists (PII, secrets,
  credentials, tokens, keys, proprietary/CUI data) and every place it can leave: HTTP
  responses, outbound API calls, logs, analytics/telemetry, error reporting, crash
  dumps, emails/notifications, file exports, third-party SDKs, and prompts/payloads
  sent to external models.
- **Egress surface & allow-listing:** outbound network calls - are destinations
  known/allow-listed, or can code call arbitrary hosts? SSRF that could be turned into
  exfiltration. Hardcoded or attacker-influenceable destinations.
- **Over-exposure in normal paths:** endpoints/queries that return more than needed
  (mass assignment, unscoped queries, verbose serializers), debug/diagnostic endpoints,
  directory listings, source maps, `.env`/backup files reachable.
- **Secrets leakage:** secrets in logs, error messages, client bundles, responses,
  URLs/query strings, or committed to the repo (cross-reference security).
- **Third-party / supply-chain egress:** what data do dependencies, SDKs, analytics,
  and model providers receive? Is it minimized and disclosed? Could a malicious
  dependency exfiltrate (cross-reference supply-chain)?
- **Data-at-rest & in-transit boundaries:** unencrypted channels or stores from which
  data could be siphoned; overly broad storage access.
- **Detection & limiting controls:** is egress logged with enough fidelity to detect
  abnormal data movement? Are there volume/rate limits on data-returning endpoints?
  Any DLP-style checks, redaction, or tokenization before data leaves?
- **Content-alteration honesty:** any truncation/sampling/transformation applied to
  data before it leaves (to a model, a store, a log) should be recorded, not silent.

## IPD emphasis

Prioritize paths that can leak secrets/credentials or bulk sensitive data, and
arbitrary-destination egress, as Blocker/High. Many mitigations (stop logging a
sensitive field, scope a query, allow-list a destination, redact before send) are low
Remediation Risk - propose by default. Distinguish repo-fixable controls from
network/infra controls (egress firewalls, DLP appliances) and route the latter to the
operator as out-of-repo notes. This lens assesses code-visible exfiltration risk, not
a live network posture.
