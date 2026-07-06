# Lens: Accessibility (WCAG 2.1 AA + terminal / text UI)

Focus the assessment on whether the user interface is usable by people with
disabilities. For graphical UIs (web, native) the standard is WCAG 2.1 AA. For
terminal / command-line / TUI output there is no formal WCAG target (WCAG is written for
web/GUI), so this lens applies the SAME underlying POUR principles to text interfaces as a
"WCAG-inspired" rubric, and says so honestly rather than claiming literal WCAG conformance
for a terminal. Assess whichever surfaces the project actually has (a project can have
both a web UI and a CLI). If the project has no UI of any kind, record that and scope this
out.

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

## Rubric for terminal / text UIs (WCAG-inspired, not literal WCAG)

Apply this whenever the project writes to a terminal: a CLI, a TUI, REPL, log output,
prompts, progress display, or ANSI-styled text. WCAG 2.1 AA does not formally cover
terminals, so these are the POUR principles translated to text interfaces. Colorblindness
affects roughly 1 in 12 men; low-vision and screen-reader users are common; and output is
frequently piped, redirected to a file, or read by another program - all of which the
styling must survive.

- **Color/style is never the ONLY signal (Perceivable).** Meaning carried solely by color
  (red = error, green = ok, yellow = warning) is invisible to colorblind users and lost
  when color is stripped. Require a redundant cue: a word/prefix (`ERROR:`/`OK:`/`WARN:`),
  a symbol, indentation, or position - so the message is complete in monochrome.
- **Faint / dim text is not load-bearing (Perceivable).** `SGR 2` (faint/dim) and
  low-intensity palettes render at very low contrast on many terminals and are a top
  low-vision complaint. Do not use dim as the only way to distinguish important text
  (secondary labels, hints, "grayed-out" but still-needed info). Dim for genuinely
  de-emphasized decoration is acceptable; dim for information the user must read is a
  finding.
- **Respect the user's and terminal's stated capability (Perceivable/Robust).** Honor the
  `NO_COLOR` convention (any value => disable color), detect non-TTY output
  (`isatty()` false when piped/redirected => plain output by default), and degrade for
  `TERM=dumb` / unset `TERM`. Support an explicit `FORCE_COLOR` override. Do not assume
  256-color or truecolor; fall back through 16-color and then no-color. Never hardcode a
  foreground color that assumes a specific background (light-on-light / dark-on-dark
  vanishes); prefer the terminal's default fg/bg and the 16 named colors, which users
  theme for their own contrast.
- **Motion, flashing, and redraw (Operable).** Spinners, rapid progress redraws, and
  `SGR 5` (blink) are hostile to some users (photosensitivity, vestibular, cognitive) and
  spam screen readers and log files. Keep animation to a TTY only, offer a quiet/plain
  mode, avoid blink entirely, and never redraw faster than needed.
- **Screen-reader and braille friendliness (Robust).** Heavy box-drawing, ASCII-art
  tables, cursor repositioning, and in-place progress bars can be unreadable or noisy under
  a screen reader. Provide a linear, plain-text alternative (labels over pure visual
  alignment; `key: value` lines the reader can follow), especially for output that conveys
  results, not just decoration.
- **Structure without visual-only cues (Understandable).** Do not rely on column alignment
  or color grouping alone to convey relationships; include labels/headers so the meaning
  survives when styling is gone.

## Preserve the polish: degrade, do not strip

Color, spinners, boxes, and styled output give command-line tools professional polish and
most users value them. Accessibility here is NOT "remove the nice things" - it is
**graceful degradation plus user control**. The preferred remedies, in order:

1. **Add the redundant cue** (symbol/label alongside color; a readable style instead of
   dim). This keeps the full experience for everyone and is low Remediation Risk - propose
   it by default.
2. **Auto-degrade on signal:** full styling on an interactive color TTY; plain text when
   `NO_COLOR` is set, output is piped/non-TTY, or `TERM` is dumb. The polished path stays
   the default for the common case.
3. **Offer an explicit toggle** when an accessible variant would MATERIALLY change the
   look/feel (e.g. disabling an animated dashboard, swapping a box-drawn layout for linear
   output). Propose an env var (`NO_COLOR`, or a project `ACCESSIBLE=1`) and/or a flag
   (`--no-color`, `--plain`, `--accessible`), documented and discoverable, rather than
   forcing the downgrade on all users.

## Interactive consult before proposing look/feel changes (this lens)

This lens still follows the harness rule: **assess and write an IPD only; never execute,
never change the project's output.** In addition, for any finding whose fix would
noticeably change the tool's visual character or professional polish (colors, spinners,
box layouts, dashboards), do not silently bake a redesign into the IPD. First **ask the
user interactively** what they want to preserve and how far to go (keep as default with
auto-degrade? gate behind a toggle? which flag/env-var name?), and record their answers
and any open trade-offs in the IPD. Small, non-visual fixes (adding an `ERROR:` prefix,
honoring `NO_COLOR`, avoiding blink) do not need this consult; a visual redesign does. If
the run is non-interactive, propose the least-disruptive option (redundant cue + honor
`NO_COLOR`/non-TTY) and list the look/feel-changing alternatives as open questions for the
user to decide, rather than assuming.

## How to verify

- **Graphical UI:** run/propose an automated checker (e.g. axe) as a gate, plus a manual
  keyboard pass and a screen-reader spot check. Automated tools catch ~30-40%; call out
  what needs manual verification.
- **Terminal / text UI:** read the code that emits styling (search for ANSI escapes and
  color libraries: raw `\x1b[`/`\033[` sequences, `SGR 2`/dim and `SGR 5`/blink, and
  helpers like colorama, chalk, rich, termcolor, `tput`). Check for: a color-enable
  decision that consults `isatty()`, `NO_COLOR`, `FORCE_COLOR`, and `TERM`; any status
  conveyed by color alone; dim/blink used for information; hardcoded fg colors that assume
  a background. Then RUN the tool three ways and compare output: (1) normal on a TTY,
  (2) piped to a file or `cat` (should drop to plain), (3) with `NO_COLOR=1` set. A tool
  that emits identical raw escape codes in all three is a finding.

## IPD emphasis

Make every proposed fix checkable with a specific target: for graphical UIs a contrast
ratio, a missing label, a focus order (propose an axe CI gate where a UI test setup
exists); for terminals a specific behavior (honor `NO_COLOR`, add an `ERROR:` prefix
beside the red, drop styling when non-TTY, replace dim as the sole cue). Most
accessibility fixes are low Remediation Risk and high user value, so propose them by
default. Flag any fix that would materially change the tool's professional look/feel as an
open question (or an interactive consult per the section above), and prefer the
degrade-plus-toggle remedy over stripping the polished experience.
