# Lens: Compliance (parameterized by regime)

Focus the assessment on conformance to one or more external compliance regimes that
apply to the project. This lens is **parameterized**: it discovers which regimes apply
(or takes them from `$ARGUMENTS`) and assesses against those, rather than assuming a
fixed regime. Assess only what is verifiable from the repository; organizational and
process controls that live outside the codebase are noted as out-of-scope-for-repo.

## Lead personas

Stakeholder (legal/regulatory/contractual risk) and the security-minded architect,
with the relevant concern persona per regime (e.g. UX/accessibility for WCAG-as-legal,
privacy for data-protection law).

## Step: determine applicable regimes

If `$ARGUMENTS` names regimes, use them. Otherwise discover applicability from the
project's domain, data, docs, and stated obligations. Common regimes and triggers:

- **Data-protection law (GDPR, CCPA/CPRA, etc.)** - if it processes personal data of
  relevant residents. (Cross-reference the privacy lens for the underlying handling.)
- **Accessibility law (ADA, Section 508, EN 301 549)** - if it is a covered UI.
  (Cross-reference the accessibility lens for the WCAG specifics.)
- **HIPAA** - protected health information.
- **PCI-DSS** - cardholder/payment data.
- **SOC 2 / ISO 27001** - security/availability controls (mostly org-level; assess the
  repo-visible slice: access control, logging/audit, secrets, change management hooks).
- **Sector/other** - FERPA, GLBA, FedRAMP, SOX, COPPA, AI-specific regulation, etc.
- **Responsible-AI / fairness** - if the system makes consequential automated
  decisions (bias, transparency, human-in-the-loop, explainability, recourse).

If none apply, record that explicitly with reasoning and stop (do not force findings).

## Rubric (per applicable regime)

- Map the regime's repo-relevant requirements to concrete, checkable items.
- Assess conformance with evidence; mark each requirement met / partial / unmet /
  org-level-out-of-repo.
- Identify the highest-risk gaps (those that create legal/contractual exposure or harm
  to people).
- Note where conformance depends on configuration or deployment, not just code.

## IPD emphasis

Be careful and honest: you are assessing technical conformance signals, not giving
legal advice - say so, and route genuinely legal determinations to the
stakeholder/counsel as open questions. Propose the concrete, repo-level changes that
move toward conformance (e.g. consent capture, retention jobs, audit logging, data
export/delete paths, access controls) by default where low Remediation Risk. Clearly
separate "the repo can fix this" from "this needs an organizational control".
