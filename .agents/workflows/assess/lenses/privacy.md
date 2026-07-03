# Lens: Privacy and data protection

Focus the assessment on how personal and sensitive data is collected, used, stored,
shared, and retained. Distinct from security: this is about *appropriate handling of
data about people*, not just keeping attackers out.

## Lead personas

Stakeholder (legal/ethical/reputational risk), architect, and the novice/end-user
whose data is at stake.

## Rubric

- **Data inventory:** what personal/sensitive data does the system touch (PII, health,
  financial, location, biometrics, children's data, credentials)? Where does it flow?
- **Data minimization:** is more collected/stored/logged than needed? Are sensitive
  fields in logs, analytics, error reports, or LLM prompts?
- **Purpose & consent:** is data used only for stated purposes? Is consent captured
  where required, and revocable?
- **Retention & deletion:** defined retention; deletion/export paths (right to be
  forgotten / portability) where applicable; backups and derived copies considered.
- **Sharing & third parties:** what leaves the system (vendors, analytics, models)?
  Is it disclosed and minimized? Data-processing boundaries respected.
- **Anonymization/pseudonymization:** used where it would reduce risk; re-identification
  risk considered.
- **Access controls on personal data:** who/what can read it; tenancy/segregation.
- **Cross-border / residency** considerations where relevant.

## IPD emphasis

Flag personal-data flows that are undocumented, over-broad, or unminimized as
high-severity. Many privacy fixes (stop logging a field, add a retention job, redact
prompts) are low Remediation Risk and should be proposed by default. Regulatory
specifics (GDPR/CCPA/HIPAA) belong to the parameterized `compliance` lens; here, focus
on sound data-handling regardless of regime, and cross-reference compliance where a
legal obligation is implicated.
