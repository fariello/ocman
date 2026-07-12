# Scaffold (guided creation of a new assessment, workflow, or command)

Treat this file as the controlling instruction for a **guided, wizard-style** way to
add a new agent workflow to this framework: a new `assess-<concern>` lens, a new
standalone workflow, or a new command. You ask what the user wants, generate the file(s)
from the existing patterns, wire them into the manifest, regenerate the command shims,
and tell the user exactly what to edit. It edits framework/authoring files only.

This is an authoring/meta workflow. It changes `.agents/workflows/` (the framework
itself), so it is exempt from the usual "do not review/modify the framework" scope
exclusion when explicitly invoked by the repo owner. Stage changes; do not commit unless
asked; never push.

## Operating principles (MUST)

- **Ask, then generate.** Gather what you need step by step, confirm the plan, then
  create files. Do not guess a name/purpose the user has not given.
- **Follow the existing patterns, do not reinvent.** Read a couple of existing lenses/
  bodies first and match their structure, tone, and cross-references (Fix Bar, personas,
  the harness). Keep each policy single-sourced (reference `../release-review/...`
  rather than duplicating it).
- **Wire it fully.** A new capability is not done until it is in the manifest AND the
  shims are regenerated. Adding a capability is: create the file(s) -> add a manifest
  row -> run the installer.
- **Idempotent + honest.** If the name already exists, stop and ask (do not overwrite).
  No em dashes in authored Markdown (repo convention). Keep it KISS - a lens is a short
  focused file, not a framework.

## Step 0: Discover the conventions (do not hardcode)

Read to match current reality:
- `.agents/workflows/index.md` - the manifest format (`command | body | lens |
  description`) and the existing rows.
- `.agents/workflows/assess/assess.md` and one or two `assess/lenses/*.md` - the lens
  shape (focus, lead personas, rubric, IPD emphasis).
- `.agents/workflows/CONTRIBUTING`-style rules if present, and `ARCHITECTURE.md`'s
  "Capability layout" section (in the repo that authors the framework).
- Confirm how to regenerate shims: the `aw` CLI (`aw install <dir>`) or, from a source
  checkout, the deprecated root shim `python3 install-workflows.py` (both drive the same
  engine; neither is copied into installed target repos).

## Step 1: Ask what to create

Offer these choices and gather the details for the chosen one:

1. **A new `assess-<concern>` lens** (most common). Ask: concern name (kebab-case, e.g.
   `observability`), one-line description, the lead personas, and the concrete rubric
   bullets. It will reuse the shared `assess` harness.
2. **A new standalone workflow** (its own body, not an assess lens - e.g. another
   reviewer or a guided wizard like setup-repo). Ask: name, purpose, whether it changes
   files or only proposes, and its steps.
3. **A new command that reuses an existing body** (e.g. a variant invocation). Ask:
   command name, which body/lens it maps to, and any default arguments.

## Step 2: Generate the file(s) from the pattern

- **assess lens:** create `.agents/workflows/assess/lenses/<concern>.md` following the
  structure of existing lenses: a focus paragraph (what this concern is and how it
  differs from adjacent lenses), "Lead personas", a concrete "Rubric" (checkable
  bullets), and "IPD emphasis" (what a good IPD for this concern contains, and the Fix
  Bar framing). Cross-reference related lenses rather than duplicating them.
- **standalone workflow:** create `.agents/workflows/<name>/<name>.md` with a controlling
  header, an "Operating principles (MUST)" block, a "Step 0: Discover" section, the
  steps, and a clear statement of what it does/does not change. Reference the Fix Bar
  and personas rather than restating them. If it needs a template or helper script, put
  it under `<name>/templates/` or `<name>/tools/`.
- **command variant:** no new body; just a manifest row pointing at an existing body
  (and lens, if applicable).

Show the user the generated file(s) and let them refine before wiring.

## Step 3: Wire it into the manifest

Add a row to the manifest table in `.agents/workflows/index.md` between the
`WORKFLOWS-MANIFEST` markers, keeping the `command | body | lens | description` columns
stable. For an assess lens the body is the assess harness and the `lens` column points
at the new lens file; for a standalone workflow the body is the new file and `lens` is
`-`. Update the human-readable description sections of `index.md` if the new capability
warrants a mention.

## Step 4: Regenerate the shims

Run the installer so the per-tool slash-command shims are generated from the updated
manifest (do NOT hand-write shims):

```
aw install . --dry-run   # preview (or, from a source checkout:
                         #   python3 /path/to/agent-workflows/install-workflows.py --dry-run --repo .)
aw install .             # apply (stages changes; never commits)
```

Confirm the new `/<command>` shims appear under `.opencode/commands/` and
`.claude/commands/`.

## Step 5: Finish

- Remind the user to update `README.md`/`ARCHITECTURE.md` if the capability set they
  describe changed, and to add a dated `DECISIONS.md` entry if this was a design
  decision (never rewrite old entries).
- Tell them exactly which file(s) to edit to refine the new lens/workflow later (the
  point is that these are simple Markdown files - easy to edit).
- Summarize what was created and wired. Stage the changes; do not commit unless asked;
  never push.
