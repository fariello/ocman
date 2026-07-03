# Lens: Threat model and security hardening

Focus the assessment on the system's overall defensive posture: enumerate the attack
surface, reason about realistic threats and how an attacker would chain them, and find
hardening gaps. This is the broad "think like an attacker, then defend in depth" pass
that complements the focused `security` lens (which drills the standard categories) and
the cyber lenses (data-exfiltration, intrusion-detection, ransomware-resilience).

## Lead personas

The security-minded architect (primary) and software engineer, with the stakeholder on
which assets matter most and what a breach would cost.

## Rubric

- **Assets & trust boundaries:** what is worth protecting (data, credentials, money,
  availability, integrity), and where do trust levels change (network edges, process
  boundaries, privilege transitions, third-party integrations)? Draw the boundaries.
- **Attack surface enumeration:** every entry point - public endpoints, CLIs, message
  consumers, file/upload intake, webhooks, deserialization points, admin interfaces,
  inter-service calls, and dependencies that run with privilege.
- **Threat enumeration (e.g. STRIDE):** Spoofing, Tampering, Repudiation, Information
  disclosure, Denial of service, Elevation of privilege - applied per boundary/entry.
- **Attack-chain reasoning:** how could small weaknesses combine (an SSRF + a metadata
  endpoint, a verbose error + an enumeration, a weak default + a privilege path)?
  Single points of catastrophic failure.
- **Defense in depth:** is security concentrated in one layer (e.g. only the UI, only
  the gateway), or layered so one failure is not total? Fail-safe (deny) defaults.
- **Least privilege everywhere:** processes, services, tokens, DB roles, file
  permissions, container capabilities - minimal and scoped.
- **Hardening of the runtime/build:** secure defaults, disabled debug in prod, security
  headers, dependency/supply-chain integrity (cross-reference supply-chain), reproducible
  builds, no dev backdoors.
- **Abuse & misuse cases:** business-logic attacks, rate/quota/spend abuse, multi-tenant
  isolation, automation/bot abuse.
- **Residual risk:** what threats are accepted, and is that acceptance explicit?

## IPD emphasis

Produce an explicit, structured threat model (assets, boundaries, entry points,
threats-per-boundary, and the chains that matter), then propose the highest-leverage
hardening - prioritizing attack chains that reach high-value assets. Cross-reference
the focused lenses rather than re-deriving their rubrics. Where a defense needs an
infrastructure or organizational control (WAF, network segmentation, IR process),
label it out-of-repo for the operator. Avoid speculative hardening with no threat
behind it (Complexity axis).
