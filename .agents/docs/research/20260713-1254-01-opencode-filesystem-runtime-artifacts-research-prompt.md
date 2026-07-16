# Deep-research prompt: OpenCode filesystem, configuration, storage, and runtime artifacts for ocman

- **Created:** 2026-07-13 12:54 America/New_York
- **Target project:** [ocman, OpenCode Manager](https://github.com/fariello/ocman)
- **Primary upstream:** [OpenCode](https://github.com/anomalyco/opencode)
- **Purpose:** Produce an exhaustive, source-grounded technical reference for the coding agent maintaining `ocman`.
- **Required output:** One standalone, downloadable Markdown file.
- **Do not modify:** `ocman` source code, tests, configuration, packaging, or documentation other than creating the requested research deliverable.

## Role

You are a senior systems researcher, cross-platform filesystem engineer, SQLite specialist, and OpenCode source-code analyst.

Your task is to determine, document, and explain every filesystem object, configuration source, persistent or transient data store, operating-system integration point, process, IPC mechanism, network listener, runtime dependency, and lifecycle behavior that OpenCode uses, creates, reads, updates, merges, migrates, caches, locks, prunes, or deletes.

The resulting report will be used by the coding agent working on `ocman`, a CLI and TUI administration, backup, restoration, recovery, cleanup, and maintenance tool for OpenCode.

Do not limit the research to artifacts that `ocman` currently manages or that you believe `ocman` should manage. The report must first describe OpenCode completely and accurately. Only after that should it analyze implications for `ocman`.

## Required deliverable

Create exactly one Markdown file named:

```text
YYYYMMDD-HHMM-opencode-filesystem-runtime-artifacts-reference.md
```

Use the current local date and time when creating the file. Place it in the current working directory unless the execution environment provides an explicit artifact-output directory. Return a direct downloadable link or otherwise clearly identify the exact path to the completed file.

Do not create or modify any other file.

The report must be self-contained, readable by a coding agent with no prior conversation context, and detailed enough to guide implementation, testing, backup, restore, cleanup, migration, diagnostics, and cross-platform path discovery in `ocman`.

## Starting context

Read the current `ocman` repository before researching OpenCode. At minimum, inspect:

- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- package source
- path and platform-discovery code
- database code
- backup and restore code
- cleanup and orphan-detection code
- session export, recovery, and compaction code
- configuration code
- tests and fixtures
- any existing architecture, implementation-plan, or research documents

Understand what `ocman` currently assumes about:

- OpenCode database paths and schemas
- SQLite WAL and SHM files
- legacy JSON storage
- session-diff files
- project and session identity
- backup composition
- restore ordering
- active-process safety
- permissions
- configuration precedence
- output and recovery directories
- temp files
- operating-system behavior

Do not treat the current `ocman` implementation as authoritative about OpenCode. Use it to identify assumptions that must be verified.

Primary project references:

- `https://github.com/fariello/ocman`
- `https://pypi.org/project/ocman/`

## Version discipline

At the beginning of the report, record all of the following:

1. Research execution date and timezone.
2. Installed OpenCode version, if OpenCode is installed.
3. Latest stable OpenCode release at research time.
4. Exact upstream Git tag and commit examined.
5. Exact `dev` or default-branch commit examined, if different.
6. Exact `ocman` commit examined.
7. Operating systems and environments actually tested.
8. Important features observed only on an unreleased branch.
9. Any minimum or historical OpenCode versions that `ocman` appears to support.

Use the latest stable release as the primary behavioral baseline. Inspect the current upstream development branch separately to identify imminent changes, but label unreleased behavior clearly.

When behavior differs across versions, document the first known version, last known version, migration behavior, and a reliable way for `ocman` to detect the applicable layout.

Do not cite moving branch URLs as though they were immutable evidence. Cite a tag or commit-specific URL whenever possible.

## Evidence hierarchy

Use evidence in this order:

1. OpenCode source code at a pinned stable release.
2. OpenCode source code at a pinned development commit, clearly labeled unreleased.
3. Official OpenCode documentation and schemas.
4. Reproducible runtime experiments in isolated environments.
5. OpenCode release notes, migrations, and tests.
6. Maintainer statements in upstream issues or pull requests.
7. Community reports only when needed to identify a possibility or discrepancy.

For every substantive statement, label the evidence as one of:

- **Documented**
- **Source-verified**
- **Empirically observed**
- **Inferred**
- **Unverified or version-dependent**

Resolve contradictions by preferring stable tagged source and reproducible observations over prose documentation. Report contradictions explicitly rather than silently choosing one account.

## Research method

### 1. Source-code tracing

Clone or inspect the exact OpenCode stable tag in a temporary location outside the `ocman` repository.

Search comprehensively for all code that:

- joins or resolves filesystem paths
- reads or writes files
- creates directories
- changes permissions or ownership
- uses XDG paths or platform-specific application directories
- reads environment variables
- opens SQLite databases
- sets SQLite pragmas
- creates WAL, SHM, journal, lock, migration, or sidecar files
- creates temporary files or directories
- performs atomic writes, renames, copies, links, or replacements
- creates sockets, named pipes, TCP listeners, UDP listeners, or mDNS services
- starts child processes
- launches shells, PTYs, LSP servers, MCP servers, formatters, Git, Bun, package managers, browsers, editors, or helper binaries
- downloads tools, models, plugins, updates, schemas, or language servers
- watches directories or files
- caches remote data
- creates snapshots, patches, hidden Git repositories, or object alternates
- imports, exports, shares, forks, compacts, reverts, or deletes sessions
- handles authentication or provider credentials
- installs, upgrades, or uninstalls OpenCode
- performs migrations from older storage layouts
- prunes, vacuums, checkpoints, garbage-collects, or invalidates caches

Trace each path from its declaration through every call site that reads, writes, deletes, migrates, or backs it up.

Inspect source areas related to at least:

- global path resolution
- configuration loading and merging
- managed configuration
- authentication
- database and schema
- legacy storage and migrations
- projects, worktrees, sessions, messages, parts, todos, and shares
- snapshots and reverts
- logs
- cache versioning
- plugins and custom tools
- agents, commands, modes, skills, themes, and plans
- rules and instruction files
- shell and PTY execution
- LSP
- MCP
- formatters
- server, web, attach, ACP, and IDE integrations
- mDNS
- updater and installer
- export and import
- desktop application behavior, where applicable
- test-only overrides that may reveal path abstractions

### 2. Isolated runtime experiments

Where feasible, run OpenCode in disposable environments with no real user secrets.

Use isolated values for `HOME`, XDG variables, temp directories, and project roots. Capture filesystem state before and after each test. Record commands exactly.

Test at least these lifecycle events where supported:

1. Installation by each supported method.
2. First invocation with no configuration.
3. First invocation in a non-Git directory.
4. First invocation at a Git worktree root.
5. Invocation from a nested project directory.
6. Invocation in a monorepo.
7. Invocation in an additional Git worktree.
8. Invocation through a symlinked path.
9. Creating a session.
10. Continuing, forking, sharing, exporting, importing, reverting, and deleting a session.
11. Running `/init`.
12. Creating global and project-local agents.
13. Creating or loading commands, skills, tools, plugins, themes, modes, and plans.
14. Installing a plugin with dependencies.
15. Invoking a language that triggers an LSP download.
16. Invoking a configured formatter.
17. Starting a local MCP server and connecting to a remote MCP server.
18. Starting TUI, `run`, `serve`, `web`, `attach`, ACP, and IDE-related modes.
19. Enabling mDNS where supported.
20. Authentication login and logout using a disposable provider or mocked credentials.
21. Automatic update check and explicit upgrade.
22. Cache invalidation after an OpenCode version change.
23. Pruning and cleanup.
24. `uninstall --dry-run`, with and without keep flags.
25. Concurrent OpenCode processes using the same data directory.
26. Abrupt termination during database and file writes.
27. Restore or startup after stale WAL, SHM, lock, temp, or partial files remain.

Use appropriate tracing tools when available:

- Linux: `strace`, `lsof`, `inotifywait`, `/proc`, `ss`, and `fuser`
- macOS: `fs_usage`, `opensnoop`, `lsof`, `nettop`, and equivalent tools
- Windows: Process Monitor, Process Explorer, `Get-Process`, `Get-NetTCPConnection`, and handle inspection
- WSL: test both Linux-side OpenCode and Windows-side OpenCode, including path interoperation where possible

Do not fabricate observations for operating systems you cannot test. For untested systems, use source analysis and label conclusions accordingly.

### 3. Repository-wide path inventory

Build a machine-assisted inventory of all hard-coded or derived paths, filenames, directory names, extensions, environment-variable overrides, and platform conditionals in OpenCode source.

Do not rely only on documentation pages or filename searches. Include paths assembled dynamically and paths created by dependencies when OpenCode intentionally invokes those dependencies.

## Mandatory scope

The report must cover every category below.

### A. Installation, binary, update, and removal artifacts

Document installation and executable locations for all supported installation methods, including where applicable:

- official install script
- npm
- pnpm
- Bun
- Homebrew
- Windows package or installer methods
- desktop application packaging
- self-update downloads and replacement behavior

For each method, identify:

- binary or shim location
- package installation location
- version metadata
- update staging files
- PATH modifications
- shell profile modifications
- caches
- permissions
- uninstall behavior
- files intentionally retained by keep flags
- artifacts that the OpenCode uninstaller does not remove

### B. Global path model and OS path resolution

Explain how OpenCode derives:

- home
- config
- data
- cache
- state
- logs
- executable cache
- temporary storage

Document XDG behavior and all relevant environment variables, including how unset, empty, relative, invalid, or conflicting values are handled.

Provide exact resolved defaults for:

- Linux
- macOS
- Windows
- WSL
- containers or headless environments, where behavior differs

Distinguish native OpenCode behavior from behavior inherited from third-party path libraries.

### C. Configuration sources and complete precedence

Provide an exact ordered precedence model for all configuration sources, including:

- remote organization configuration such as `.well-known/opencode`
- global `opencode.json`
- global `opencode.jsonc`
- legacy global configuration filenames
- TUI configuration
- `OPENCODE_CONFIG`
- `OPENCODE_TUI_CONFIG`
- `OPENCODE_CONFIG_DIR`
- project configuration discovered from the current directory upward
- nested project configuration
- `.opencode` configuration directories
- `OPENCODE_CONFIG_CONTENT`
- inline permission configuration
- system-managed configuration on Linux, macOS, and Windows
- macOS managed preferences or MDM profiles
- command-line flags
- defaults compiled into OpenCode

For every layer, explain:

- whether it is optional
- search start and stop boundaries
- whether traversal follows symlinks
- behavior inside and outside Git
- behavior with nested repositories and worktrees
- whether multiple files are loaded or only the first match
- whether later sources override, merge, append, or coexist
- whether invalid files abort startup or are skipped
- whether missing files are silently ignored
- whether project files can override managed settings
- whether remote configuration is cached, and where
- whether environment-provided content is persisted

Create a field-level merge-semantics table. Determine, from source, how OpenCode merges:

- scalars
- objects
- nested objects
- arrays
- plugin lists
- MCP definitions
- agents
- commands
- permissions
- provider settings
- model settings
- instructions
- null values
- explicit false values
- duplicate identifiers

Do not summarize precedence only at a high level. Show at least three worked examples with conflicting values across several layers and state the final resolved result.

### D. Project and worktree discovery

Explain how OpenCode identifies:

- current directory
- project directory
- Git root
- Git common directory
- worktree
- repository identity
- global or catch-all project
- nested repository
- bare repository
- non-Git directory
- deleted or moved worktree
- symlinked worktree
- Windows path with drive letter
- UNC path
- WSL-mounted Windows path

Document how project identity is stored and how it changes if a repository is moved, cloned, reinitialized, rebased, or used through another worktree.

Explain any implications for `ocman` project grouping, orphan detection, path matching, and restore.

### E. Project-local and global customization trees

Inventory every supported child of `.opencode/`, `~/.config/opencode/`, `OPENCODE_CONFIG_DIR`, and any compatible convention.

At minimum, investigate:

- `agents/` and legacy singular aliases
- `commands/`
- `modes/`
- `plugins/`
- `skills/`
- `tools/`
- `themes/`
- `plans/`
- `package.json`
- lockfiles
- `node_modules/`
- generated `.gitignore`
- local configuration files
- TUI configuration
- any hidden metadata or migration files

For each directory or file, document:

- exact canonical name
- aliases and backward compatibility
- recursive or nonrecursive discovery
- allowed extensions
- filename-to-identifier rules
- frontmatter or schema requirements
- validation and startup-failure behavior
- load order
- duplicate handling
- automatic creation trigger
- automatic modification trigger
- whether OpenCode ever deletes it
- whether it should normally be committed to Git
- external dependencies it can cause OpenCode to install
- permissions or executable-bit requirements
- backup and restore significance

Also cover compatible trees and fallbacks such as:

- `.agents/`
- `.claude/`
- user-global equivalents
- `AGENTS.md`
- `CLAUDE.md`
- custom instruction files and globs
- remote instruction URLs

Clearly distinguish fallback behavior from additive behavior.

### F. Persistent application data

Inventory all persistent files and directories under OpenCode’s data location.

Include, where present:

- primary SQLite database
- database schema version
- migration metadata
- WAL
- SHM
- rollback journal
- temporary SQLite files
- projects
- sessions
- messages
- parts
- todos
- session shares
- accounts
- workspaces
- provider or model metadata
- legacy JSON storage
- session-diff files
- logs
- auth data
- snapshots
- exported sessions
- imported sessions
- recovery or compaction artifacts created by OpenCode itself
- crash or diagnostic artifacts
- statistics or usage data
- installation metadata

For every item, explain:

- schema or format
- identifier relationships
- lifecycle
- creation trigger
- update trigger
- deletion trigger
- migration history
- referential integrity
- whether deletion cascades
- whether files may become orphaned
- whether the item is authoritative, derived, cached, or regenerable
- backup requirements
- restore ordering
- safe-copy requirements
- sensitive-data classification
- expected ownership and permissions

### G. SQLite behavior and concurrency

Document the exact database path and SQLite opening mode.

Determine and report:

- journal mode
- synchronous mode
- foreign-key behavior
- busy timeout
- locking behavior
- connection pooling
- checkpoint behavior
- vacuum behavior
- schema migrations
- transaction boundaries
- crash recovery
- concurrent-reader and concurrent-writer behavior
- how long WAL and SHM files may remain
- whether OpenCode can run multiple processes against one database
- whether OpenCode provides an API or command suitable for consistent backup
- whether direct copying is safe while OpenCode is running
- when DB, WAL, and SHM must be copied as a family
- whether SQLite online backup, `VACUUM INTO`, or process quiescence is preferable
- risks of deleting sidecars
- risks of restoring only part of the database family
- database corruption detection and recovery behavior

Map every table relevant to sessions, projects, messages, parts, todos, shares, accounts, and workspaces. Show key relationships and cascade rules.

### H. Legacy and migration layouts

Identify every historical on-disk layout still detected, read, migrated, or left behind by current OpenCode.

For each migration:

- source layout
- destination layout
- trigger
- marker file or schema version
- idempotency
- partial-failure behavior
- cleanup behavior
- compatibility window
- whether old data remains after success
- how `ocman` should detect and handle it

Include legacy configuration filenames, singular directory aliases, JSON storage, old database names, old snapshot layouts, and deprecated compatibility conventions.

### I. Snapshots, patches, undo, redo, and reverts

Explain OpenCode’s snapshot implementation in detail.

Document:

- snapshot root path
- project and worktree keying
- hidden Git repository layout
- Git object storage
- alternates files
- index files
- exclude files
- ignored-file behavior
- large-file behavior
- symlink behavior
- cleanup and prune intervals
- relationship to session messages and patch metadata
- how undo and redo use snapshots
- what happens when repositories move
- what can safely be deleted
- what must be backed up for session restoration or historical undo
- potential interactions with the user’s real `.git` directory
- concurrency and locking

### J. Authentication, secrets, and sensitive files

Inventory all credentials, API keys, OAuth tokens, refresh tokens, cookies, account metadata, and server passwords that OpenCode persists or reads.

For each:

- exact path
- file format
- environment override
- expected permission mode
- whether permissions are enforced or merely requested
- behavior on Windows ACLs
- behavior if permissions are too open
- rotation and logout behavior
- backup sensitivity
- restore sensitivity
- redaction requirements
- whether the content may appear in logs, exports, crash reports, or backups

Verify any use or non-use of OS keychains, credential managers, or secure enclaves.

### K. Cache and downloaded dependencies

Inventory all cache content, including:

- plugin packages
- Bun or npm dependencies
- language servers
- formatter binaries
- model lists
- provider metadata
- icons and themes
- downloaded OpenCode binaries
- update payloads
- schemas
- remote configuration
- web assets
- temporary package-manager state
- cache-version marker files

For each cache:

- path
- keying
- invalidation
- versioning
- size-growth behavior
- concurrent access
- safe deletion
- automatic recreation
- network consequences of deletion
- whether user-authored plugin data can accidentally reside there

### L. Logs, diagnostics, and telemetry-adjacent data

Document:

- log directory
- filename pattern
- rotation
- retention
- verbosity controls
- stderr logging
- structured or unstructured format
- crash logs
- trace files
- diagnostic bundles
- server access logs
- child-process output capture
- redaction behavior
- sensitive-data risks
- pruning behavior

Distinguish local logs from remote telemetry, sharing, or provider request records.

### M. Temporary files and atomic-write behavior

Inventory all use of the OS temp directory and any temp directories under OpenCode paths.

Document:

- filename patterns
- export/import staging
- download staging
- plugin installation staging
- update staging
- atomic-write temporary files
- lock files
- stale-file cleanup
- crash leftovers
- permissions
- symlink and race protections
- cleanup on normal exit versus abnormal termination

### N. Runtime processes and child processes

Create an exhaustive process tree and lifecycle description for each OpenCode mode.

Include:

- CLI parent process
- TUI
- local server
- web UI
- attach client
- ACP server or client
- IDE integration
- shell commands
- PTYs
- Git
- Bun
- npm or package installation
- plugins
- custom tools
- LSP servers
- local MCP servers
- formatters
- browser launchers
- updater
- desktop helpers
- any background workers

For each process type, document:

- executable discovery
- parent and child relationship
- working directory
- inherited environment
- stdin, stdout, and stderr handling
- PTY use
- pipes
- process groups
- signal handling
- cancellation behavior
- timeout behavior
- orphan risk
- shutdown ordering
- files held open
- database connections held open
- network listeners
- restart behavior
- platform differences

### O. IPC, sockets, ports, pipes, and network listeners

Document every local communication mechanism used by OpenCode:

- TCP
- UDP
- HTTP
- HTTPS
- WebSocket
- SSE
- mDNS
- Unix-domain sockets
- Windows named pipes
- anonymous pipes
- PTY file descriptors
- stdio-based MCP
- stdio-based ACP
- IDE communication channels

For each mechanism, identify:

- creating command or mode
- default bind address
- default or selected port
- random-port behavior
- port-discovery mechanism
- authentication
- CORS behavior
- password environment variables
- state or discovery files
- collision handling
- listener lifetime
- exposure risk on non-loopback interfaces
- whether `ocman` should detect an active listener before maintenance

Do not assume a socket or named pipe exists merely because it is common in similar tools. Verify each mechanism.

### P. File watchers and filesystem event behavior

Document any watcher implementation, watched roots, ignore rules, platform backend, descriptor usage, startup scans, event coalescing, and experimental flags.

Explain whether backup, restore, mass deletion, or atomic replacement by `ocman` can trigger OpenCode reloads, races, or inconsistent state while OpenCode is active.

### Q. Permissions, ownership, ACLs, and filesystem semantics

For every security-sensitive or operationally important artifact, document:

- creation mode
- effect of user umask
- chmod behavior
- ownership expectations
- root or administrator requirements
- Windows ACL behavior
- read-only filesystem behavior
- network filesystem behavior
- NFS or SMB concerns
- case sensitivity
- case preservation
- path-length limits
- Unicode normalization
- reserved Windows names
- symlinks
- hard links
- junctions
- mount points
- sparse files
- file locking portability
- atomic rename assumptions
- cross-device rename behavior

Identify any code paths vulnerable to TOCTOU, symlink substitution, archive path traversal, permission widening, or partial restore.

### R. OS-specific matrix

Provide a full comparison for:

- Linux
- macOS
- Windows
- WSL
- containers and CI environments, when relevant

Include exact paths, environment variables, installation methods, shell selection, path normalization, permissions, locks, process signals, PTYs, sockets, package caches, managed configuration, and uninstall behavior.

For WSL, distinguish:

- Linux OpenCode operating inside WSL
- Windows OpenCode invoked from Windows Terminal or an IDE
- Windows files accessed through `/mnt/<drive>`
- Linux files accessed through `\\wsl$`
- mixed-path configuration
- Git and shell executable selection
- risk of two OpenCode installations using different data stores for the same repository

### S. Desktop, CLI, server, web, IDE, and ACP differences

Determine whether each frontend or operating mode uses the same:

- config
- data
- database
- auth
- cache
- logs
- plugin location
- server process
- session model
- project identity
- update mechanism

Document any mode-specific files, processes, ports, caches, or migrations.

### T. Environment variables and command-line flags

Create a complete table of every environment variable and CLI flag that changes filesystem, process, network, security, persistence, or discovery behavior.

Include undocumented variables found in source.

Columns must include:

- name
- type
- default
- scope
- read location in source
- affected artifacts or behavior
- precedence
- persistence
- security significance
- version introduced, if known

### U. Plugin and extension side effects

Explain that plugins, custom tools, skills, commands, MCP servers, formatters, LSP servers, and provider integrations can create arbitrary files or processes beyond OpenCode’s core inventory.

Still document what OpenCode itself guarantees or controls:

- load paths
- dependency installation
- execution context
- working directory
- environment
- permissions
- lifecycle hooks
- cache location
- error handling
- duplicate loading
- pure or no-plugin mode

Define the boundary between core OpenCode artifacts and extension-owned artifacts.

### V. Backup, restore, cleanup, and deletion classification

Classify every artifact into one of:

1. **Must back up for full restoration**
2. **Should back up, but can be reconstructed**
3. **Optional user-authored configuration**
4. **Sensitive secret requiring protected backup**
5. **Derived or regenerable**
6. **Transient and normally excluded**
7. **Unsafe to copy while OpenCode is active**
8. **Unsafe to restore while OpenCode is active**
9. **Safe to delete when OpenCode is stopped**
10. **Safe to delete at any time**
11. **Unknown or extension-owned**

For each artifact, state:

- whether backup should preserve permissions, timestamps, symlinks, and ownership
- consistency requirements
- restore order
- conflict behavior
- version compatibility
- path relocation behavior
- post-restore validation
- whether OpenCode must be stopped
- whether an active-process check is sufficient
- whether a lock should be acquired
- whether `ocman` should refuse, warn, snapshot, or proceed

### W. Implications and recommendations for ocman

Only after completing the OpenCode reference, provide an `ocman` implications section.

Review the current `ocman` implementation against the verified OpenCode behavior and identify:

- correct assumptions
- stale assumptions
- missing artifacts
- unsafe backup behavior
- unsafe restore behavior
- unsafe cleanup behavior
- incorrect path precedence
- cross-platform gaps
- version-detection gaps
- permission-preservation gaps
- active-process and locking gaps
- database consistency gaps
- secret-handling gaps
- symlink or archive-extraction risks
- plugin and extension boundaries
- opportunities for diagnostic commands
- opportunities for a machine-readable artifact manifest

For each recommendation, include:

- issue
- evidence
- affected OpenCode versions
- affected operating systems
- user impact
- risk level
- proposed `ocman` behavior
- implementation notes
- test requirements
- confidence
- whether it is essential, advisable, or merely optional

Do not recommend a change merely to appear thorough. Recommend changes only when they materially improve correctness, safety, compatibility, recoverability, or maintainability.

## Required report structure

Use this exact top-level structure:

```text
# OpenCode Filesystem, Configuration, Storage, and Runtime Artifacts Reference for ocman

## 1. Executive summary
## 2. Research scope, versions, and evidence
## 3. OpenCode architecture relevant to filesystem management
## 4. Master artifact inventory
## 5. OS path-resolution matrix
## 6. Configuration discovery, precedence, and merge semantics
## 7. Project, repository, and worktree discovery
## 8. Project-local and global customization trees
## 9. Persistent application data
## 10. SQLite database, sidecars, migrations, and concurrency
## 11. Legacy storage and migration layouts
## 12. Sessions, projects, messages, parts, todos, and shares
## 13. Snapshots, patches, undo, redo, and revert storage
## 14. Authentication and sensitive data
## 15. Caches and downloaded dependencies
## 16. Logs, diagnostics, temp files, and atomic writes
## 17. Processes, PTYs, child processes, and shutdown behavior
## 18. IPC, sockets, pipes, ports, mDNS, and network listeners
## 19. File watchers and live-reload behavior
## 20. Permissions, ownership, ACLs, links, and filesystem semantics
## 21. Installation, upgrade, uninstall, and residual artifacts
## 22. Desktop, CLI, TUI, server, web, IDE, and ACP differences
## 23. Environment-variable and command-line control surface
## 24. Plugin and extension-owned artifacts
## 25. Backup, restore, cleanup, and deletion policy matrix
## 26. Findings and recommendations for ocman
## 27. Proposed ocman test matrix
## 28. Version-drift and compatibility strategy
## 29. Unknowns, contradictions, and areas requiring further testing
## 30. Source and evidence index
```

## Mandatory tables

Include at least the following tables.

### Master artifact inventory

Columns:

| Artifact | Path expression | Linux | macOS | Windows | WSL | Read/write/delete | Creation trigger | Format/schema | Sensitive | Permissions | Locking/concurrency | Lifecycle | Precedence role | Backup class | Safe deletion | Version notes | Evidence |

### Configuration precedence table

Columns:

| Priority | Source | Search rule | Multiple files? | Merge behavior | Can be overridden by | Invalid-file behavior | Persisted? | Evidence |

### Merge-semantics table

Columns:

| Configuration field/type | Earlier value | Later value | Final value | Rule | Source evidence | Empirical confirmation |

### Runtime-resource table

Columns:

| Mode or feature | Process | Child executable | CWD | stdio/PTY | IPC/network | Files held open | Shutdown behavior | OS differences | Evidence |

### Backup and restore policy table

Columns:

| Artifact | Include by default | Consistency method | Preserve metadata | Secret handling | Restore order | Active-process policy | Cross-version concerns | Validation |

### ocman recommendation register

Columns:

| ID | Finding | Risk | Affected platforms/versions | Recommendation | Priority | Required tests | Confidence |

## Required diagrams

Use Mermaid diagrams where they improve precision. Include at least:

1. Configuration precedence and merge flow.
2. OpenCode process and IPC topology.
3. Persistent storage relationships.
4. Backup and restore ordering.
5. Project/worktree/session identity relationships.

Ensure the Markdown remains understandable without Mermaid rendering.

## Citation requirements

Every nontrivial factual claim must be cited.

For source-code citations, link to immutable tag- or commit-specific GitHub URLs and identify:

- repository
- path
- symbol or function
- line range, where possible
- tag or commit

For runtime observations, provide:

- OS
- OpenCode version
- command
- environment overrides
- observed result
- relevant trace excerpt or summarized evidence

For official documentation, cite the exact page and access date.

Do not rely on uncited statements such as “OpenCode usually” or “it appears.” Either verify the behavior or label it unresolved.

## Accuracy and safety rules

- Do not expose real credentials, tokens, session content, private prompts, or user data.
- Use disposable homes, repositories, databases, and credentials for experiments.
- Do not run destructive commands against the user’s real OpenCode environment.
- Do not delete, vacuum, migrate, restore, or uninstall the user’s actual OpenCode installation.
- Do not treat issue proposals as implemented behavior.
- Do not treat documentation examples as proof of source behavior when source can be inspected.
- Do not assume Linux paths apply to macOS or Windows.
- Do not assume CLI and desktop behavior are identical.
- Do not assume all `.opencode/` children are created automatically.
- Do not assume a path is backed up merely because it is under the OpenCode data directory.
- Do not assume a cache is safe to delete if extensions may store user-authored state there.
- Do not assume copying only the SQLite main file produces a consistent backup.
- Do not recommend direct file manipulation while OpenCode is active without analyzing locks, open handles, watchers, and database state.

## Quality bar

The report is complete only if a coding agent can use it to answer all of the following without additional research:

1. What does OpenCode read, create, update, and delete on each supported OS?
2. Which paths are authoritative, derived, cached, transient, sensitive, or extension-owned?
3. Exactly how are configuration files discovered, ordered, merged, and overridden?
4. Which project-local files and directories are recognized, and which are auto-created?
5. What data belongs to a project, worktree, session, message, or global installation?
6. How does OpenCode store and migrate sessions and related records?
7. How can `ocman` make a consistent backup while respecting SQLite WAL behavior?
8. What must be stopped or locked before cleanup, backup, restore, migration, or vacuum?
9. What permissions and metadata must be preserved?
10. What differs among Linux, macOS, Windows, WSL, CLI, desktop, TUI, server, web, IDE, and ACP?
11. What processes, PTYs, pipes, sockets, ports, watchers, and child services can remain active?
12. What OpenCode artifacts can safely be deleted and recreated?
13. What historical layouts must `ocman` recognize?
14. What current `ocman` assumptions are materially incorrect or incomplete?
15. How should `ocman` detect future OpenCode layout and schema drift?

## Final validation checklist

Before completing the deliverable:

- Verify that every required top-level section exists.
- Verify that every mandatory table exists.
- Verify that all path examples distinguish path expressions from resolved paths.
- Verify that stable and unreleased behaviors are separated.
- Verify that every OS claim is either tested or source-derived and labeled.
- Verify that every recommendation traces back to evidence.
- Verify that no real secrets or private session content appear.
- Verify that no source file other than the requested Markdown deliverable was modified.
- Verify that the output filename follows the required timestamped convention.
- Return the exact file path and a direct download link if the environment supports one.
