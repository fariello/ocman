# Lens: Generalization, extensibility, and configurability (productization)

Focus on how ready the project is to be reused, deployed, administered, and maintained
by people other than its author, across organizations, tenants, and environments.
Distinct from the `architecture` lens (structural soundness); here the question is
productization and reuse. Cross-references `security` for authz/secrets. Do not
generalize for its own sake; over-generalization is a finding too.

## Lead personas

Productization reviewer and software architect (primary), the DevOps/operator who
deploys and runs it, the stakeholder judging broader-deployment readiness, and the
novice administrator taking a clean handoff.

## Rubric

- **Abstraction candidates:** logic/integrations coupled to one org, tenant, vendor,
  workflow, or auth provider. Recommend the fitting boundary (interface/adapter/
  provider/strategy/policy/plugin/config schema) with the concrete reuse benefit.
- **Hard-coded values that should be configuration:** names, domains, URLs, hosts,
  ports, paths, regions, buckets, emails, role names, thresholds, fiscal/timezone/
  locale/currency, limits, branding. Name the mechanism per value (env var / config /
  typed setting / tenant / org / admin-editable / secret / documented default / stays).
- **Extensibility seams:** business logic out of routes/views; injectable dependencies;
  integrations behind adapters; workflow/status/role logic that should be data-driven.
- **Configuration architecture:** coherent separation of required/optional/secret/
  deployment/tenant/admin/feature-flag settings; startup validation; `.env.example`;
  safe defaults; no environment-specific behavior baked into source.
- **Administration and operability (clean handoff):** setup/bootstrap, migration safety,
  seed/demo data separated from production, health/readiness, structured logs/audit,
  backup/restore and upgrade docs. Can someone other than the author run and upgrade it?
- **Org/deployment-specific assumptions and multi-tenant readiness:** for each, decide
  remain-concrete / rename-generic / configurable / tenant-scoped / move-to-docs /
  move-to-seed-demo / extension-point. What breaks if the org, domain, auth provider, or
  region changed?
- **Security as administrable (see `security` lens):** centralized default-deny authz,
  not scattered checks; no hard-coded superusers or org-email gating; secrets via a
  manager; defaults safe for dev and prod.
- **KISS counterweight (Complexity axis):** flag speculative configurability and
  unnecessary abstraction as strongly as missing seams. Over- and under-generalization
  are both findings.

## IPD emphasis

Map each finding onto the "concrete / config / admin-editable / tenant / feature-flag /
adapter / documented-default / defer" spectrum, gated by the Fix Bar's Complexity axis:
propose the smallest change that unlocks real reuse, not a productization rewrite.
Productization refactors often carry high Remediation Risk (broad blast radius, contract
changes), so prefer staged paths, name the invariants a refactor must preserve and route
them to characterization tests, and send large redesigns (multi-tenancy, a config
framework) to open questions with a sketch, not a big-bang change. Never recommend
removing a project-specific feature merely because it is specific.
