# Lens: Ransomware resilience

Focus the assessment on whether the system can withstand and recover from a
ransomware-style event - data encrypted/destroyed/held hostage - with minimal loss.
The repo-visible aspects are backup/recovery code, data immutability, blast-radius
limits, and integrity verification. Organizational backup operations and endpoint
protection are out-of-repo and routed to the operator.

## Lead personas

Architect and operator (recovery/continuity), with the stakeholder on acceptable data
loss / downtime and the security view on the attack path (cross-reference reliability,
security, and intrusion-detection).

## Rubric

- **Backups exist and are code-visible:** is there backup logic or documented backup
  procedure for the data the system owns? Frequency vs. acceptable loss (RPO).
- **Backup immutability & isolation:** are backups append-only / write-once / versioned
  / offline or in a separate trust domain, so the same compromise cannot also encrypt
  or delete them? A backup the app can overwrite is not ransomware-resilient.
- **Restore is real and tested:** is there a restore path, and is it exercised (a
  backup you have never restored is a hope, not a backup)? Recovery runbook present;
  RTO considered.
- **Data versioning / soft-delete:** append-only or versioned stores, soft-delete with
  retention, point-in-time recovery - so encryption/deletion is reversible.
- **Blast-radius limits:** least privilege on write/delete paths; a single
  compromised credential/service cannot rewrite or destroy all data; segmentation of
  data stores; scoped tokens; no broad delete/overwrite capability on the hot path.
- **Integrity verification:** checksums/hashes/signatures that would reveal silent
  tampering or mass encryption; the live-interaction data-integrity class
  (overwrite-of-verified-output) from the runbook applies.
- **Detection linkage:** would mass-encryption/mass-delete activity be detectable
  (cross-reference intrusion-detection and logging-audit)?
- **Key/secret resilience:** if encryption keys are lost/stolen, what is the recovery
  story; key custody and rotation (cross-reference security).

## IPD emphasis

Prioritize the two things that most determine ransomware survival: **immutable/isolated
backups** and a **tested restore**. Then blast-radius reduction (least-privilege write
paths) and versioning/soft-delete. Many of these are repo-addressable and low-to-medium
Remediation Risk - propose by default; flag those that depend on infrastructure
(offline backup vaults, immutable object storage, EDR) as out-of-repo operator
actions. This lens assesses code/architecture resilience, not your backup operations
or endpoint security.
