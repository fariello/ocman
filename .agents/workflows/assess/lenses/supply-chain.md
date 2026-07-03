# Lens: Dependencies, licensing, and supply chain

Focus the assessment on the third-party code the project depends on and the integrity
of how it is obtained and built: vulnerabilities, license compatibility, dependency
health, and build provenance.

## Lead personas

Software engineer and the security-minded architect, with the stakeholder on legal
(licensing) and operational (abandoned deps) risk.

## Rubric

- **Known vulnerabilities:** run/propose a vulnerability scan of the dependency tree
  (direct and transitive); flag known-vulnerable versions and propose upgrades.
- **License compatibility:** every dependency's license is compatible with the
  project's license and distribution model; no copyleft surprise in a permissive
  product; missing/unknown licenses flagged. Stakeholder/legal decision where unclear.
- **Dependency health:** abandoned/unmaintained packages, single-maintainer risk,
  deprecated packages, packages far behind upstream.
- **Dependency hygiene:** unused dependencies; duplicated/overlapping libraries;
  oversized deps pulled in for trivial use; could a small need be met without a new
  dependency (KISS / Complexity axis)?
- **Pinning & reproducibility:** lockfiles present and committed; versions pinned
  appropriately; reproducible installs; integrity hashes where supported.
- **Provenance & integrity:** sources trusted; no typosquat-prone names; build pulls
  from expected registries; no curl-pipe-to-shell in build steps.
- **SBOM:** is a software bill of materials produced or producible where it matters?
- **Update strategy:** is there a process/automation for keeping deps current safely?

## IPD emphasis

Propose security upgrades and license-conflict resolutions as high priority. Adding a
dependency is itself a Complexity/security cost - so for "missing capability" findings,
prefer the lightest safe option and justify any new dependency. Most hygiene fixes
(pin a version, remove an unused dep, add a scan to CI) are low Remediation Risk;
propose by default. Route license decisions with legal ambiguity to open questions.
