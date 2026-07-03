# Lens: Accessibility (WCAG 2.1 AA)

Focus the assessment on whether the user interface is usable by people with
disabilities, targeting WCAG 2.1 AA conformance. Applies to any UI (web, native,
terminal where relevant). If the project has no UI, record that and scope this out.

## Lead personas

UI/UX engineer and the complete-novice/end-user - including users relying on screen
readers, keyboard-only navigation, magnification, and reduced motion.

## Rubric (WCAG 2.1 AA, organized by POUR)

- **Perceivable:** text alternatives for non-text content; captions/transcripts for
  media; meaningful sequence and structure; color is not the only signal; **contrast
  >= 4.5:1 normal text, >= 3:1 large text and non-text/UI/focus indicators**, verified
  in light AND dark themes; text resizes to 200% without loss; reflow at 320px.
- **Operable:** full keyboard operability with no traps; visible focus indicators;
  logical focus order; targets large enough; no content that flashes more than 3x/sec;
  sufficient time / no unexpected timeouts; skip links and landmarks for navigation.
- **Understandable:** language set; predictable behavior (no surprise context
  changes on focus/input); labels and instructions for inputs; clear, specific error
  identification and suggestions.
- **Robust:** valid, semantic HTML5 (or platform-native accessibility APIs); correct
  ARIA roles/states/properties only where semantics are insufficient; name/role/value
  exposed to assistive tech; status messages announced.

## How to verify

Prefer concrete checks: run/propose an automated checker (e.g. axe) as a gate, plus a
manual keyboard pass and a screen-reader spot check. Automated tools catch ~30-40%;
call out what needs manual verification.

## IPD emphasis

Make every proposed fix checkable with a specific target (a contrast ratio, a missing
label, a focus order). Propose an axe CI gate where a UI test setup exists. Most
accessibility fixes are low Remediation Risk and high user value, so propose them by
default; flag any that require design decisions as open questions.
