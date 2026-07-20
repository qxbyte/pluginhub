<p align="right"><strong>English</strong> | <a href="./README.zh-CN.md">中文</a></p>

# pluginhub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./README.md#license)
[![specode](https://img.shields.io/badge/specode-6.5.1-blue.svg)](./plugins/specode/.claude-plugin/plugin.json)
[![task-swarm](https://img.shields.io/badge/task--swarm-0.12.1-blue.svg)](./plugins/task-swarm/.claude-plugin/plugin.json)
[![obsidian-wiki](https://img.shields.io/badge/obsidian--wiki-2.2.1-blue.svg)](./plugins/obsidian-wiki/.claude-plugin/plugin.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2)](https://github.com/qxbyte/pluginhub#installation)
[![CodeBuddy](https://img.shields.io/badge/CodeBuddy-2.97.1%2B-1E90FF)](https://github.com/qxbyte/pluginhub#installation)
[![Tests](https://img.shields.io/badge/pytest-301%20cases-success)](./plugins/task-swarm/tests)

> qxbyte's plugin marketplace for CLI coding agents
> (Claude Code / CodeBuddy / Codex / Kimi).

**pluginhub** is a small plugin marketplace: add it once, then install
any plugin it hosts. More plugins will land here over time.

## Plugins

| Plugin | Version | What it does |
| --- | --- | --- |
| **specode** | 6.5.1 | Lightweight spec-driven **workflow** orchestration shell — walks a host agent through requirements → design → tasks → execute → acceptance, delegating each phase to [superpowers](https://github.com/obra/superpowers) skills with a first-class specode-native fallback, and landing 4 fixed docs per spec (requirements / design / tasks / implementation-log). Bundles dedicated `intake` and `execute` skills (the execution tail is manually triggerable anytime via `/specode:execute`), a zero-import task-swarm handoff for parallel execution, and optional locate-oriented experience retrieval. Version history is in the [CHANGELOG](./plugins/specode/CHANGELOG.md). |
| **task-swarm** | 0.12.1 | Standalone multi-agent **orchestration** driven by a `pipeline.yml` — semantic task groups with cross-group concurrency, forked coders, and per-group reviewer + validator loops (`state.json` is the single source of truth). specode delegates its execution phase here; also runnable directly via `/task-swarm:swarm`. See [`plugins/task-swarm/`](./plugins/task-swarm) + its CHANGELOG. |
| **obsidian-wiki** | 2.2.1 | Maintain an Obsidian LLM-Wiki via three skills — a deterministic structure layer (`wiki-struct`), content curation (`wiki-curate`), and a unified orchestrator (`wiki-orchestrate`). Generic code + per-vault config in the home-dir registry `~/.config/obsidian-wiki/` (fallback: `<vault>/.wiki/config.json`), zero hardcoded structure. See [`plugins/obsidian-wiki/`](./plugins/obsidian-wiki). |
| **ragkit** | 0.2.2 | Standalone knowledge-base **RAG** — vector + lexical + metadata three-channel recall, RRF-fused, returns pointer cards. Optional downstream consumer of specode `distill` output; zero heavy deps (stdlib + numpy for lexical mode). See [`plugins/ragkit/`](./plugins/ragkit). |

`## Installation` covers the whole marketplace; the other sections
(Highlights, Usage, Architecture) document **specode**, the flagship
plugin. For **task-swarm**, see its sources and `CHANGELOG` under
[`plugins/task-swarm/`](./plugins/task-swarm); for **obsidian-wiki**,
see its own `README.md` / `AGENTS.md` under
[`plugins/obsidian-wiki/`](./plugins/obsidian-wiki).

## Highlights

- **Orchestration shell, not a state machine.** specode delegates each
  phase to a mature superpowers skill (`brainstorming` → `writing-plans`
  → `subagent-driven-development` / `executing-plans` →
  `verification-before-completion`). It owns only what's uniquely its
  own: the spec lifecycle, fixed-doc landing, and the task-swarm bridge.
- **Works standalone (native fallback).** No superpowers? specode runs
  the clarify / plan / execute / verify loop itself with `AskUserQuestion`
  wizards and sequential TDD. The native path is a first-class peer, not
  an afterthought.
- **4 fixed documents, fixed names, fixed location.** Every spec
  produces `requirements.md` / `design.md` (传统设计文档: architecture /
  modules / interfaces / data flow) / `tasks.md` (the executable plan,
  engine-neutral) / `implementation-log.md` under `<specsRoot>/<slug>/` —
  whatever engine generated the content. Bug fixes use prose in
  `requirements.md` (no `bugfix.md`).
- **Documents are the state.** No persistent session files, no locks,
  no status footer, no logging. "Which phase am I in?" is inferred from
  which fixed docs exist plus the `- [ ]` checkbox progress in
  `tasks.md` (5.x legacy specs: `design.md`).
- **One adaptive selector.** After `tasks.md` is confirmed, an
  `AskUserQuestion` selector offers up to 4 execution paths — only the
  ones whose engine is installed: 委托 task-swarm / superpowers
  subagent-driven / superpowers executing-plans / specode 自执行.
- **First-run specsRoot setup.** On first use specode asks once for your
  document directory and uses it **verbatim** as the specs root, then
  persists it to `~/.config/specode/config.json.specsRoot` and never
  asks again.
- **One lightweight hook.** A single advisory `SessionStart` hook reminds
  the agent specode is available. No blocking, no per-turn machinery.
- **Parallel execution is a separate plugin.** Pick "委托 task-swarm" and
  specode reads `tasks.md`, derives a `pipeline.yml`, and hands off to
  the standalone **task-swarm** plugin (zero import).
- **Project-level constraints follow the chain.** specode + task-swarm
  (AI-EDS v0.9 痛点 #14 方案 D, preserved into v4.0.0 / v0.10.0) scan
  `CLAUDE.md` / `AGENT.md` / `AGENTS.md` / `CODEBUDDY.md` at
  `<project_root>`, its parent directory, and any subdir touched by
  `@writes`, and surface the matched **absolute paths** (not content)
  into both `requirements.md` (`## 项目级约束`) and every coder /
  reviewer / validator `task.md` (`## 项目级约束（必读）`).
  `_PROJECT_AGENT_DOCS.md` inbox sentinel reinforces the hard
  constraint. Fixes the silent drop where independent subagent
  processes never see the host agent's auto-loaded instruction files.
- **Two inputs, nothing else to configure.** specode's only persistent
  state is the specsRoot config (`~/.config/specode/config.json`, or the
  `SPECODE_ROOT` env override) and each spec's `project_root` (its
  `requirements.md` frontmatter, the single source of truth read by every
  downstream step). No defaults file, no autonomous-mode env-var knobs —
  every `AskUserQuestion` gate simply asks.
- **Location-oriented knowledge, not memory injection.** The old AI-EDS
  memory-injection pipeline (specode P3-1 `codemap recall` + P3-2
  rule-check + acceptance auto-distill, plus task-swarm `cmd_resolve`
  auto-ingest writing `.ai-memory/knowledge/*.yml`) was removed in
  v4.0.0 / v0.10.0 after baseline experiments (3 cases) showed the
  recall round-trip did not net save token; neither plugin reads /
  writes `.ai-memory/knowledge/`. **v5.1.0 reintroduced retrieval on a
  deliberately different, pointers-not-facts footing**: run
  `/specode:distill <slug>` manually to sediment atomic
  case / navigation knowledge points into the project's own
  `<project_root>/knowledge-base/` (gitignored; optional copy to an
  Obsidian dir you specify), and the requirements / design phases run a
  two-tier gated retrieval over its small `MEMORY.md` index to locate
  real code faster — real code stays the sole source of truth, and
  execution / task-swarm receive zero injection.
  To restore v3.4.0 / v0.9.2 behaviour: `git checkout backup/specode-v3.4.0-task-swarm-v0.9.2`.

## Installation

> 📌 **Marketplace name is `pluginhub` (the repo name), not `qxbyte` (the owner name).**
> All install / uninstall commands use `<plugin>@pluginhub`, e.g. `specode@pluginhub` and `task-swarm@pluginhub`. Using `@qxbyte` will fail with `Marketplace "qxbyte" not found`. Cached plugins are also stored under `~/.claude/plugins/cache/pluginhub/<plugin>/<version>/` — useful when troubleshooting which version is actually loaded.

### From GitHub (recommended)

Works across four hosts. **Claude Code** and **CodeBuddy** are supported
and verified (CodeBuddy on 2.97.1). **Codex** ships experimental manifests
whose install syntax is unverified. **Kimi Code** is **local-clone only**
(it cannot install a monorepo plugin from a URL) — see
[Kimi Code (local install)](#kimi-code-local-install) below and
[Multi-host support](#multi-host-support).

```sh
# Claude Code
claude plugin marketplace add https://github.com/qxbyte/pluginhub
claude plugin install specode@pluginhub

# CodeBuddy
codebuddy plugin marketplace add https://github.com/qxbyte/pluginhub
codebuddy plugin install specode@pluginhub

# Codex (unverified)
codex plugin marketplace add qxbyte/pluginhub
codex plugin install specode@pluginhub

# Kimi Code — NOT a URL install; see "Kimi Code (local install)" below.
```

For the full superpowers-backed experience, also install the
**superpowers** plugin. For multi-agent parallel execution, also install
**task-swarm** from this same marketplace (no second `marketplace add`
needed) — specode delegates the execution phase to it when installed, and
self-executes sequentially otherwise:

```sh
# Claude Code
claude plugin install task-swarm@pluginhub
# CodeBuddy
codebuddy plugin install task-swarm@pluginhub
```

specode runs fine without either via its native fallbacks.

### Kimi Code (local install)

Kimi Code **cannot install pluginhub from a GitHub URL** — neither a bare
repo URL (`/plugins install https://github.com/qxbyte/pluginhub`) nor a
remote marketplace URL (`/plugins marketplace https://…/marketplace.json`).
Kimi does not support installing a plugin from a monorepo **subdirectory**,
and its scan only handles a single top-level plugin dir (confirmed against
Kimi Code's docs + source). Install from a **local clone** instead:

```sh
# 1) Clone anywhere; note the ABSOLUTE path to the clone.
git clone https://github.com/qxbyte/pluginhub

# 2) In a Kimi session, install each plugin you want by ABSOLUTE local path:
/plugins install /ABS/PATH/TO/pluginhub/plugins/specode
/plugins install /ABS/PATH/TO/pluginhub/plugins/task-swarm
/plugins install /ABS/PATH/TO/pluginhub/plugins/ragkit
/plugins install /ABS/PATH/TO/pluginhub/plugins/obsidian-wiki

#    …or browse all four via the local marketplace file, then install them:
/plugins marketplace /ABS/PATH/TO/pluginhub/.kimi-plugin/marketplace.json

# 3) Start a fresh session — Kimi loads plugin changes on NEW sessions only.
/new
```

- The path **must be absolute**; a relative path fails with
  `Plugin root must be an absolute path`.
- Kimi **copies** the plugin into its managed dir at install time, so
  re-run the install after you `git pull` to pick up updates.
- On Kimi the session advisory is injected via each manifest's
  `sessionStart.skill` (`using-specode` / `using-ragkit`) — there is no
  `SessionStart` hook. task-swarm / obsidian-wiki have no session advisory
  (their skills are still found by Kimi's native scan).
- A future one-command remote install is possible by shipping per-plugin
  release-asset zips (Kimi accepts zip-URL sources) — not yet set up.
- **Verified on a real Kimi host:** the local **marketplace-browse** install
  (`/plugins marketplace <abs>/.kimi-plugin/marketplace.json`) succeeds and
  `/specode:spec` triggers specode. Still unconfirmed: the `sessionStart.skill`
  auto-advisory (so far specode is triggered by typing its command, not by the
  model proactively knowing) and the end-to-end flows of the other three plugins.

### One-shot (Claude Code only)

```sh
claude --plugin-url https://github.com/qxbyte/pluginhub/archive/refs/heads/main.zip
```

### Local development

```sh
git clone https://github.com/qxbyte/pluginhub.git
claude    --plugin-dir ./pluginhub/plugins/specode
codebuddy --plugin-dir ./pluginhub/plugins/specode

# add task-swarm too if you want delegated multi-agent execution
claude --plugin-dir ./pluginhub/plugins/specode --plugin-dir ./pluginhub/plugins/task-swarm
```

### Uninstall

```sh
claude plugin uninstall specode@pluginhub
claude plugin uninstall task-swarm@pluginhub   # if installed
claude plugin marketplace remove pluginhub
# optional: wipe user-level config (and legacy ~/.specode state)
rm -rf ~/.specode ~/.config/specode
```

### Update

```sh
# Claude Code
claude plugin update specode@pluginhub
claude plugin marketplace update pluginhub

# CodeBuddy
codebuddy plugin update specode@pluginhub
codebuddy plugin marketplace update pluginhub
```

### Multi-host support

Every plugin ships **four** independent host manifests, so each host
installs and adapts on its own. Skills prose is single-source and
host-neutral (tool names like `AskUserQuestion` / `Skill` / `Agent` /
`Task` are kept, and each SKILL carries a top "Host-tool convention"
fallback note); the `SessionStart` hook handler is one file shared by
all hosts (the nested `hookSpecificOutput.additionalContext` shape is
accepted by Claude / CodeBuddy / Codex), and the only per-host
difference is the manifest's hook env var.

| Host | Per-plugin manifest | Root catalog | Hooks env var | Status |
| --- | --- | --- | --- | --- |
| Claude Code | `<plugin>/.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` | `${CLAUDE_PLUGIN_ROOT}` (`hooks/hooks.json`) | supported |
| CodeBuddy | `<plugin>/.codebuddy-plugin/plugin.json` | `.codebuddy-plugin/marketplace.json` | `${CODEBUDDY_PLUGIN_ROOT}` (`hooks/hooks.codebuddy.json`) | supported |
| Codex | `<plugin>/.codex-plugin/plugin.json` | `.agents/plugins/marketplace.json` | `${PLUGIN_ROOT}` (`hooks/hooks.codex.json`, matcher `startup\|resume\|clear`) | experimental — unverified |
| Kimi | `<plugin>/.kimi-plugin/plugin.json` | `.kimi-plugin/marketplace.json` (Kimi schema: `version` `"2"` + `id`/`source`) | — (`sessionStart.skill`, no hooks) | local-clone only — install + specode trigger **verified**; `sessionStart` advisory unconfirmed |

Codex and Kimi are wired but **not yet verified on a real host**. Open
items:

- **Codex** — the `.codex-plugin/plugin.json` `skills` / `hooks` field
  usage and relative-path resolution are not verified on a real Codex host.
- **Codex** — the hooks env var is assumed to be `${PLUGIN_ROOT}` (it may
  actually be `CODEX_PLUGIN_ROOT` or another name); unverified.
- **Codex** — the marketplace landing at `.agents/plugins/marketplace.json`
  with a string `owner` schema is unverified.
- **Kimi** — a **bare repo URL cannot install a monorepo subdir plugin**
  (confirmed against Kimi Code's docs + source: no subpath GitHub install,
  no multi-subdir scan). So pluginhub on Kimi is **local-clone only**: clone,
  then `/plugins marketplace <abs>/.kimi-plugin/marketplace.json` (its `source`
  entries resolve to the plugin subdirs) or `/plugins install <abs>/plugins/<name>`.
  For remote/one-command install a future option is per-plugin release-asset
  zips (Kimi accepts zip-URL sources). **SessionStart on Kimi is handled by the
  manifest's `sessionStart.skill`** — specode/ragkit load `using-specode` /
  `using-ragkit` (a bootstrap advisory skill) at session start; the other two
  plugins have no session advisory (skills are found by Kimi's native scan).
  The end-to-end flow is **not yet verified on a real Kimi host**.
- The base-directory-relative path `../../scripts/run.sh` used inside
  skills is not verified reachable under Codex / Kimi.
- specode's cross-skill "invoke by name" (the `Skill` tool) has no
  verified equivalent under Codex / Kimi.
- Codex's `ask_user_question` being Plan-mode-only may affect specode's
  执行方式 selector; unverified.
- task-swarm's `agents/*.md` are Claude-style agent files; Codex custom
  subagents are TOML, which this round did not convert — multi-agent
  isolation under Codex is unverified.

## Usage

specode has exactly five commands.

### 1. Start a spec

```sh
/specode:spec <requirement>
```

`cd` to your project directory first — specode derives the default
project root from the cwd (`git rev-parse --show-toplevel`, falling
back to cwd) and asks you to confirm it once per spec. On the **first
ever** run it also asks once for your document management directory
and remembers it. The agent then walks the pipeline:

1. **requirements** — the `specode:intake` skill (specode's own, always)
   runs project analysis (agent-docs scan + experience retrieval +
   reading the located real code) → analysis-driven clarification →
   writes `requirements.md` with the frontmatter contract (`spec_id` /
   `created_at` / `project_root`). This is also the **primary node for
   ragkit/experience retrieval**.
2. **design** — produce a traditional design doc `design.md`
   (architecture / modules / interfaces / data flow / error handling /
   test strategy) via `superpowers:brainstorming` (design only) or native
   authoring.
3. **tasks** — produce the executable plan `tasks.md` (via
   `superpowers:writing-plans`, or native Task breakdown). Engine-neutral:
   every execution path consumes this one file.
4. **执行方式 selector** — pick how to execute (adaptive 4 options; see
   Highlights).
5. **execute** — run the plan with TDD, appending to
   `implementation-log.md`.
6. **verify** — check against the `requirements.md` `AC-N` items, the
   design's 测试策略, and the `tasks.md` checkboxes, then ask you to
   accept.

All output lands under `<specsRoot>/<slug>/` as the 4 fixed documents.

### 2. Resume a spec

```sh
/specode:continue <slug>
```

`<slug>` is required. specode locates `<specsRoot>/<slug>/`, infers
the phase from the documents present (and the `- [ ]` progress in
`tasks.md`; 5.x legacy specs: `design.md`), **reports a progress brief,
then stops and waits** — say "继续" to resume, or supply requirement
changes first. It never auto-resumes. Use `/specode:list` to find a slug.

### 3. Run the execution tail

```sh
/specode:execute <slug>
```

Run (or resume) a spec's execution tail at any time: presents the 执行方式
selector (task-swarm / superpowers / specode-native), dispatches the chosen
engine, then runs acceptance. The spec pipeline and `/specode:continue` route
here automatically once `tasks.md` is ready; invoke it manually after a
session break. Requires `tasks.md` (or a legacy 5.x `design.md` plan) to
exist — it never generates the plan itself.

### 4. List specs

```sh
/specode:list
```

Lists every spec under `<specsRoot>` with its inferred phase. Overview
only — it does not resume.

### 5. Distill knowledge (off-pipeline)

```sh
/specode:distill <slug> [--target-dir <abs-path>]
```

Manually sediments a finished spec (plus the current agent context)
into atomic **case / navigation knowledge points** under the project's
own `<project_root>/knowledge-base/` (cases/ + navigation/ + a
`MEMORY.md` index, gitignored), optionally copying them to an Obsidian
directory. The requirements / design phases later retrieve these as
**location pointers, never facts** — real code stays the sole source
of truth. Never auto-run; the acceptance phase only offers it.

## Architecture

```
.claude-plugin/marketplace.json   marketplace manifest (specode + task-swarm + obsidian-wiki)
plugins/specode/
  .claude-plugin/plugin.json      plugin manifest
  hooks/hooks.json                1 advisory SessionStart hook
  scripts/
    resolve_root.py               specsRoot / project_root / defaults CLI
    knowledge.py                  knowledge-base index CLI (MEMORY rebuild/validate/copy-to)
    spec_hooks.py                 SessionStart discipline injection
    run.sh / run.cmd              python3 → python → py interpreter probe
  skills/spec/                    /specode:spec — orchestration shell (pipeline engine + new-spec entry)
    SKILL.md                      requirements → design → tasks → hand off to execute
    references/
      selectors.md                first-time directory-setup question
      obsidian.md                 specsRoot path resolution + conventions
      superpowers-wiring.md       phase ↔ superpowers skill mapping
      retrieval.md                experience retrieval spec (intake primary node)
      knowledge-flow.md           one-page knowledge-loop mental model
  skills/continue/                /specode:continue <slug> — load-and-stop + documents-as-state inference
  skills/execute/                 /specode:execute <slug> — execution tail (selector → dispatch → acceptance), also invoked by spec/continue
    references/selectors.md       执行方式 selector verbatim example
  skills/list/                    /specode:list — list specs with inferred phase
  skills/intake/
    SKILL.md                      requirements phase engine (analysis + clarify + write)
  skills/distill/                 /specode:distill — user-invocable skill (no command), off-pipeline
    SKILL.md                      knowledge-base sedimenter (case/navigation points)
    references/                   breakdown heuristics + doc templates
  assets/templates/               requirements.md / design.md / tasks.md /
                                  implementation-log.md seed templates
  tests/                          hermetic pytest suite (resolve_root.py + knowledge.py)
```

The companion **task-swarm** plugin (`plugins/task-swarm/`) is a
standalone multi-agent orchestrator that specode optionally hands off
to; see its own `skills/swarm/SKILL.md` and `CHANGELOG.md`. The
**obsidian-wiki** plugin (`plugins/obsidian-wiki/`) is self-contained
and documented by its own `README.md` / `AGENTS.md`.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the stdlib-only
runtime rule, the `run.sh` CLI invocation contract, the advisory-hook
rule, hermetic test conventions, and the release procedure.

## License

MIT
