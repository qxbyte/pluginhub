<p align="right"><strong>English</strong> | <a href="./README.zh-CN.md">中文</a></p>

# pluginhub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./README.md#license)
[![specode](https://img.shields.io/badge/specode-3.3.1-blue.svg)](./plugins/specode/.claude-plugin/plugin.json)
[![task-swarm](https://img.shields.io/badge/task--swarm-0.7.3-blue.svg)](./plugins/task-swarm/.claude-plugin/plugin.json)
[![obsidian-wiki](https://img.shields.io/badge/obsidian--wiki-2.0.0-blue.svg)](./plugins/obsidian-wiki/.claude-plugin/plugin.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2)](https://github.com/qxbyte/pluginhub#installation)
[![CodeBuddy](https://img.shields.io/badge/CodeBuddy-2.97.1%2B-1E90FF)](https://github.com/qxbyte/pluginhub#installation)
[![Tests](https://img.shields.io/badge/pytest-152%20cases-success)](./plugins/task-swarm/tests)

> qxbyte's plugin marketplace for CLI coding agents
> (Claude Code / CodeBuddy).

**pluginhub** is a small plugin marketplace: add it once, then install
any plugin it hosts. More plugins will land here over time.

## Plugins

| Plugin | Version | What it does |
| --- | --- | --- |
| **specode** | 3.3.1 | A lightweight spec-driven **workflow** — an orchestration shell that delegates each phase to [superpowers](https://github.com/obra/superpowers) skills (with a first-class native fallback) and lands 3 fixed docs per spec. 3.x adds AI-EDS knowledge integration: step 2.2 injects `codemap recall` hits (rules / pitfalls / cases / code maps) into `requirements.md`, and v3.3.1 (痛点 #14 方案 D) also lists scanned `CLAUDE.md / AGENT.md / AGENTS.md / CODEBUDDY.md` paths as a `## 项目级约束` section so design / downstream subagents inherit project-level constraints. Documented below. |
| **task-swarm** | 0.7.3 | Multi-agent **orchestration** driven by a `pipeline.yml`: semantic task groups with cross-group concurrency, fork coders, per-group reviewer + validator loops. 0.7.x lands AI-EDS feedback loop (P2-1 `ingest_lessons` writes `case-*` / `pit-*` to `.ai-memory/knowledge/` + `knowledge-base/*.md` via `codemap knowledge write`), frontmatter-first `project_root`, registry-based run lookup that survives cwd drift, and v0.7.3 (痛点 #14 方案 D) inserts a `## 项目级约束（必读）` section listing scanned `CLAUDE.md / AGENT.md` paths into every coder / reviewer / validator `task.md` so independent subagent processes don't silently miss them. See [`plugins/task-swarm/`](./plugins/task-swarm). |
| **obsidian-wiki** | 2.0.0 | Maintain an Obsidian LLM-Wiki: deterministic structure layer (Home tree / READMEs / partition pages), SpecIn → knowledge-base distillation + MEMORY, content curation (lint / ingest / curate), unified orchestrator. Generic + per-vault `.wiki/config.json`. See [`plugins/obsidian-wiki/`](./plugins/obsidian-wiki). |

`## Installation` covers the whole marketplace; the other sections
(Highlights, Usage, Architecture) document **specode**, the flagship
plugin. For **task-swarm**, see its sources and `CHANGELOG` under
[`plugins/task-swarm/`](./plugins/task-swarm).

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
- **3 fixed documents, fixed names, fixed location.** Every spec
  produces `requirements.md` / `design.md` / `implementation-log.md`
  under `<specsRoot>/<slug>/` — whatever engine generated the content.
  Bug fixes use prose in `requirements.md` (no `bugfix.md`).
- **Documents are the state.** No persistent session files, no locks,
  no status footer, no logging. "Which phase am I in?" is inferred from
  which fixed docs exist plus the `- [ ]` checkbox progress in
  `design.md`.
- **One adaptive selector.** After `design.md` is confirmed, an
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
  specode reads `design.md`, derives a `pipeline.yml`, and hands off to
  the standalone **task-swarm** plugin (zero import).
- **Project-level constraints follow the chain.** v3.3.1 + task-swarm
  0.7.3 (AI-EDS v0.9 痛点 #14 方案 D) scan `CLAUDE.md` / `AGENT.md` /
  `AGENTS.md` / `CODEBUDDY.md` at `<project_root>`, its parent
  directory, and any subdir touched by `@writes`, and surface the
  matched **absolute paths** (not content) into both `requirements.md`
  (`## 项目级约束`) and every coder / reviewer / validator `task.md`
  (`## 项目级约束（必读）`). Fixes the silent drop where independent
  subagent processes never see the host agent's auto-loaded
  instruction files.

## Installation

> 📌 **Marketplace name is `pluginhub` (the repo name), not `qxbyte` (the owner name).**
> All install / uninstall commands use `<plugin>@pluginhub`, e.g. `specode@pluginhub` and `task-swarm@pluginhub`. Using `@qxbyte` will fail with `Marketplace "qxbyte" not found`. Cached plugins are also stored under `~/.claude/plugins/cache/pluginhub/<plugin>/<version>/` — useful when troubleshooting which version is actually loaded.

### From GitHub (recommended)

Works with either CLI; the plugin manifest is shared.
CodeBuddy verified on 2.97.1.

```sh
# CodeBuddy
codebuddy plugin marketplace add https://github.com/qxbyte/pluginhub
codebuddy plugin install specode@pluginhub

# Claude Code
claude plugin marketplace add https://github.com/qxbyte/pluginhub
claude plugin install specode@pluginhub
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

### One-shot (Claude Code only)

```sh
claude --plugin-url https://github.com/qxbyte/pluginhub/archive/refs/heads/main.zip
```

### Local development

```sh
git clone https://github.com/qxbyte/pluginhub.git
claude    --plugin-dir ./specode/plugins/specode
codebuddy --plugin-dir ./specode/plugins/specode

# add task-swarm too if you want delegated multi-agent execution
claude --plugin-dir ./specode/plugins/specode --plugin-dir ./specode/plugins/task-swarm
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

## Usage

specode has exactly three commands.

### 1. Start a spec

```sh
/specode:specode-spec <requirement>
```

`cd` to your project directory first — specode uses the current
terminal cwd as the project root (no prompt). On the **first ever**
run it asks once for your document management directory and remembers
it. The agent then walks the pipeline:

1. **requirements** — clarify + write `requirements.md` (via
   `superpowers:brainstorming`, or a native `AskUserQuestion` wizard).
2. **design** — produce an executable plan `design.md` (via
   `superpowers:writing-plans`, or native Task breakdown).
3. **执行方式 selector** — pick how to execute (adaptive 4 options; see
   Highlights).
4. **execute** — run the plan with TDD, appending to
   `implementation-log.md`.
5. **verify** — check against the design's test points and the
   `requirements.md` `AC-N` items, then ask you to accept.

All output lands under `<specsRoot>/<slug>/` as the 3 fixed documents.

### 2. Resume a spec

```sh
/specode:specode-continue <slug>
```

`<slug>` is required. specode locates `<specsRoot>/<slug>/` and infers
the phase from the documents present (and the `- [ ]` progress in
`design.md`), then continues from there. Use `/specode:specode-list` to
find a slug.

### 3. List specs

```sh
/specode:specode-list
```

Lists every spec under `<specsRoot>` with its inferred phase. Overview
only — it does not resume.

## Architecture

```
.claude-plugin/marketplace.json   marketplace manifest (specode + task-swarm)
plugins/specode/
  .claude-plugin/plugin.json      plugin manifest (version 2.0.0)
  hooks/hooks.json                1 advisory SessionStart hook
  commands/specode-spec.md        /specode:specode-spec (new spec)
  commands/specode-continue.md    /specode:specode-continue <slug>
  commands/specode-list.md        /specode:specode-list
  scripts/
    resolve_root.py               specsRoot resolution + persistence + list
    spec_hooks.py                 SessionStart discipline injection
    run.sh / run.cmd              python3 → python → py interpreter probe
  skills/specode/
    SKILL.md                      the orchestration shell (all behavior)
    references/
      selectors.md                执行方式 selector verbatim examples
      obsidian.md                 specsRoot path resolution + conventions
      superpowers-wiring.md       phase ↔ superpowers skill mapping
  assets/templates/               requirements.md / design.md /
                                  implementation-log.md seed templates
  tests/                          hermetic pytest suite (resolve_root.py)
```

The companion **task-swarm** plugin (`plugins/task-swarm/`) is a
standalone multi-agent orchestrator that specode optionally hands off
to; see its own README and `CLAUDE.md`.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the stdlib-only
runtime rule, the `run.sh` CLI invocation contract, the advisory-hook
rule, hermetic test conventions, and the release procedure.

## License

MIT
