# templates

Source templates the installer copies or generates into target repositories - NOT
workflows themselves. Edit a template here to change what installed repos receive.

Includes: `shim-README.md` (written into the generated `.opencode/`/`.claude/` command
dirs), `workflow-artifacts-README.md` (written into `workflow-artifacts/`), and the
`agents-README.md` / `plans-README.md` / `plans-<bucket>-README.md` files used to
scaffold the `.agents/` and `.agents/plans/` directory READMEs. All are written
no-clobber (a target's existing file is never overwritten).
