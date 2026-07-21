# Workflow: handoff (session-continuity resume-document generator)

Capture the EPHEMERAL SESSION CONTEXT of the current session into a resume document so a fresh
session (a different agent, or the same agent cold) can pick up exactly where this one left off,
after context loss, compaction, a crash, or a deliberate new session.

Run this WITHIN an active, context-rich session. Its value is preserving what is NOT on disk: the
conversation, the decisions and reasoning, the approaches tried and abandoned, the corrections
caught, and how the maintainer wants work done. A fresh agent can already read `DECISIONS.md`,
`TODO.md`, the plans board, and the code; it cannot recover this session's discussion. So `/handoff`
is PRIMARILY a session-context capturer; the on-disk record is only a thin supporting frame.

## What this workflow does and does not do

- It PRODUCES one markdown resume document and writes it to the gitignored quarantine lane
  `.agents/prompts/local/` (see "Output" below). It is read-only with respect to all product code
  and the durable record.
- It does NOT `git add`, stage, commit, or push the handoff. Making it durable/tracked is the
  human's deliberate decision (the file can hold raw session context). It runs no other workflow.

## Memory kernel

Re-read before drafting and before the exit gate:

1. Session context is the CORE; the on-disk record is a thin supporting frame (pointers, not
   re-summaries). Do not pad the doc with a filesystem summary a fresh agent could produce itself.
2. Apply the Sensitivity and privacy contract to EVERYTHING you write (below). The input is raw
   conversation, the output is a durable, pushable file: classify, then omit / reframe-and-confirm /
   never-raw-secrets.
3. Write to `.agents/prompts/local/` only. Never auto-stage or commit. The human promotes.
4. Run `aw check-local-leaks` on the finished file before you are done.
5. If run cold (little live session context), say so plainly; do not invent nuance.

## Inputs

`$ARGUMENTS`, if present, is an optional focus note (a topic or emphasis for the handoff). Otherwise
capture the whole session.

## Step 1: Gather the session context (the core)

From YOUR working memory of this session (not the disk), collect:

- What we were mid-doing and WHY we paused; the next intended move.
- Decisions/agreements made verbally this session that are not yet in `DECISIONS.md`.
- Approaches TRIED and ABANDONED, and why (so the next session does not repeat them).
- Corrections or overclaims caught this session (so the corrected version is inherited).
- The nuance layer (Step 2).

## Step 2: Harvest the nuance (working style, preferences, the why)

Actively record the tacit layer a naive summary loses:

- Maintainer working preferences (how they want work done): e.g. prefer installed tools over
  hand-rolled code; ask-first via the interactive `question` tool with the recommendation first and
  without leaking a gate's verdict; value honest pushback over agreement; encode surveyed state in
  the filesystem; read files in large windows; token/context economy.
- The WHY behind the current direction and the alternatives rejected (cross-reference `DECISIONS`
  entries by number) so the next session does not relitigate or silently reverse it.
- Future intentions / roadmap: the ordered Sets, headline features, sequencing and dependencies.
- Repo-boundary and environment rules: directories not to enter; how cross-repo writes work
  (permission prompt); which sibling agents can be consulted and how (inter-agent comms).
- Inter-agent comms lever if in use: that `.agents/comms/` exists, who has been driven, that
  delivery is currently manual, and the untrusted-payload stance (D81).

If the session has little live context (cold invocation), synthesize what you can from the record and
EXPLICITLY flag "live-session nuance unavailable; derived from the record only." Never fabricate
preferences.

## Step 3: Draw the thin supporting frame (pointers, not re-summaries)

Add only what a resuming session needs to orient - POINT to the record, do not re-derive it:

- Repo facts: dir, remote, branch, unpushed-commit state, versioning mechanism, untracked-not-ours.
- Where to read the record: current highest `DECISIONS.md` D-number + any unsettled decisions;
  `TODO.md` / `CHANGELOG.md` / plans-board pointers ("read these; here is what is in flight").
- Current work state: what is done, what is in flight, what is blocked and on what.
- Designed-but-unbuilt roadmap: the Sets, sequencing.
- Known bugs (or "none open").
- In-flight EXTERNAL threads (e.g. a human-owned disclosure awaiting a reply; anything waiting on a
  third party or another agent).
- Comms inbox status (with the untrusted-payload reminder).
- Test state AS CONTEXT: capture the actual current state (e.g. "tests red mid-fix because X"), which
  is more useful than a green checkmark. Do not run the suite as a ritual; `/handoff` is about
  transferring context, not closing out the project (a repo mid-work is fine to hand off).

## Sensitivity and privacy contract (MANDATORY)

The input is raw conversation (the most sensitive, least-filtered content) and the output is a
durable, pushable file. While drafting:

1. CLASSIFY as you write. Treat as sensitive: secrets/credentials/tokens/keys; personal, career,
   health, legal, financial, or family matters; other people's names or private info; candid /
   venting remarks, criticism of people or orgs, or anything embarrassing or reputationally risky if
   public; internal/confidential business context; and machine/identity leaks (home paths,
   usernames, private repo names, hostnames, session ids - the D92/D93 class).
2. For each sensitive item, in order:
   a. NOT needed for continuity -> OMIT it; leave at most a neutral pointer ("there is out-of-repo
      context the human holds; ask them if it becomes relevant"). Never restate the content in the
      pointer.
   b. Needed for context -> REFRAME to the minimum non-sensitive form, then use the interactive
      `question` tool to get the human's approval of the exact wording, or their choice to omit. Do
      not write the reframed version durably until the human approves.
   c. Raw secrets/credentials -> NEVER write them, reframed or not; reference by location only.
3. When in doubt about an item, ASK rather than write it.

## Output

Write ONE document to `.agents/prompts/local/YYYYMMDD-HHMM-NN-session-handoff-<slug>.md` (slug is a
short focus, or `resume`). Create the `local/` dir if absent (`mkdir -p .agents/prompts/local`); it is
gitignored so nothing there can be committed. Front-matter: `Kind: session-handoff`, `Status: draft`,
date, purpose, and a "read this first" line. Order the body so the session-context core leads:

1. Header (`Kind: session-handoff`, date, purpose, read-this-first).
2. Session context (Step 1) - the main body.
3. Working style, preferences, and nuance (Step 2).
4. How to use this / recommended first moves (an ordered short list).
5. Open decisions not yet settled (options + "get the human's call, do not relitigate").
6. Supporting on-disk frame (Step 3): repo facts, where to read the record, work state, roadmap,
   known bugs, external threads, comms inbox status.
7. Workflow history line.

Omit any section only with an explicit "N/A because ..." line.

Structural reference (SHAPE only, not facts): `.agents/prompts/pending/20260717-1950-01-session-handoff-resume-here.md`
is a hand-authored example of the sections and the nuance layer. Copy its structure, never its
(now-stale) specifics.

## Exit gate (satisfy every item before reporting done)

- [ ] The session-context + nuance sections are substantive and DOMINATE (not a filesystem summary).
- [ ] Every required section is present or explicitly "N/A because ...".
- [ ] The Sensitivity and privacy contract was applied: sensitive items omitted, or reframed WITH
      the human's approval of the wording; no raw secrets; when unsure, asked.
- [ ] The file is in `.agents/prompts/local/`, `Kind: session-handoff`, `Status: draft`.
- [ ] `aw check-local-leaks <the file>` (or `python -m agent_workflows check-local-leaks .`) run and
      any hit resolved.
- [ ] NOT staged, committed, or pushed. No product-code change.
- [ ] Told the human the output path and that promoting it to durable/tracked is their call
      (`git mv` a reviewed, scrubbed copy into a tracked bucket like `.agents/prompts/pending/`).

## Reminders

- Read-only w.r.t. product code and the durable record. Never auto-commit the handoff.
- Session context first; the record is a thin supporting frame.
- `/whatnext` is the short actionable "what to do next" ordering; `/handoff` is the fuller narrative
  snapshot for full continuity. Reuse the same survey sources `/whatnext` gathers from.
