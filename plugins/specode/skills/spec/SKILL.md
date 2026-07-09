---
name: spec
description: Use when creating a new spec-driven workflow — the /specode:spec entry that walks requirements → design → tasks → 执行方式 → execute → acceptance, autonomously calling superpowers skills for the heavy lifting with a first-class specode-native fallback, and filing 4 fixed artifacts (requirements.md / design.md / tasks.md / implementation-log.md) under the user document directory. Trigger /specode:spec <request>, or 进入 spec 模式 with a new requirement.
---

# /specode:spec — create a new spec (orchestration shell)

specode is no longer a state machine. It is an **orchestration shell** that handles only its own distinctive value: the spec lifecycle, fixed on-disk artifacts, "documents-as-state" phase inference, and handing the execution tail (the `执行方式` selector → execution → acceptance, including the task-swarm handoff bridge) to the sibling `specode:execute` skill. The heavy lifting (clarification, design, TDD execution, acceptance) is done by **autonomously calling superpowers** skills in the matching phase; when superpowers is absent, **specode-native fallback** takes over. There is no persistent session file, no multi-window locking, no spec config file, no status-summary footer line, no forced code-doc sync nagging, and no session log collection.

## Activation Guard

Activate only when the current user input is `/specode:spec <request>`, or the user explicitly asks to start a **new** spec ("use spec mode" / "按 spec 流程做" / equivalent, together with a fresh requirement). Otherwise **do not activate**; handle as normal conversation. (Resuming an existing spec is the sibling `/specode:continue` skill; listing is `/specode:list`.)

There is **no session file** — whether a spec is active is inferred entirely from the **current conversation context** (which slug is running this turn) plus the **documents under `<specsRoot>/<slug>/`**. No persistent state file is ever read.

## Core invariant 🔒

Regardless of the execution engine (superpowers, task-swarm, or specode-native), a spec's artifacts are **always** the 4 documents below, with **fixed filenames**, **filed in a fixed location** at `<specsRoot>/<slug>/`. The engine only decides *who generates the content*; it never changes the artifacts' shape, naming, or location.

| Document | Fixed filename | Content |
|---|---|---|
| Requirements | `requirements.md` | Prose spec: background / why · scope (in/out) · acceptance `- [ ] AC-N` · open questions. Pure natural language, no formalized clause syntax. |
| Design | `design.md` | **Traditional design doc** (per the `assets/templates/design.md` sections): 背景与目标 / 架构概览（方案取舍）/ 模块划分与职责 / 接口设计 / 数据流 / 错误处理 / 测试策略. Prose + diagrams only — no checkboxes, no TDD steps. |
| Plan | `tasks.md` | superpowers writing-plans executable-plan format: `Goal` / `Architecture` / `Tech Stack` + `## Task N` (each Task carries `**Files:**` file scope, `**Interfaces:**` Consumes/Produces contracts, `验证: AC-N` back-reference to requirements, `(needs: Task N)` dependencies, and `- [ ]` TDD steps). Engine-neutral — all four execution engines consume this one file. |
| Execution log | `implementation-log.md` | Appended during execution: design deviations / key decisions / final acceptance summary. |

Bug fixes do not get a separate `bugfix.md` — write Current / Expected directly in `requirements.md` as prose. `pipeline.yml` is generated only temporarily when delegating to task-swarm; it is not a fixed artifact.

## specsRoot resolution (read on every start; ask only once if missing)

**Every time specode starts, first call `resolve_root.py get-root` via run.sh to read specsRoot.** `get-root` has three outcomes: **exit 0** → reachable root, use it silently; **exit 3** → not configured (typically first use) → ask via `AskUserQuestion` then `set-root`; **exit 4** → configured **but unreachable** (external drive not mounted / path moved or deleted) → the resolved path is a phantom, so **do not proceed with it** — tell the user it's unreachable and **re-prompt for a path** (mount + retry, or provide a new absolute path → `set-root`). Once a reachable root is set, all sessions use it silently, never prompting again.

All specode CLIs **must** go through the `run.sh` wrapper. The scripts live in the plugin's `scripts/` directory — relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an absolute one (do **not** resolve env vars, do **not** `find` the cache). Never call a bare `python3 <script>`:

```bash
sh ../../scripts/run.sh ../../scripts/resolve_root.py <verb> <args...>
```

(`run.sh` probes `python3 → python → py`.) The full **verb table** (`get-root` / `set-root` / `list-specs` / `resolve|write|read-project-root` / `plan-unchecked` / `doctor`) lives in `references/obsidian.md`.

**project_root single-source-of-truth rule 🔒**: project_root lives in exactly one place — the spec's `requirements.md` frontmatter. The `specode:intake` skill writes it once (via `write-project-root`); every later phase and downstream skill (distill, task-swarm) obtains it via `read-project-root`. No component re-derives it from cwd / workdir / guessing.

**First-time setup / unreachable re-prompt flow**: `get-root` exits **3** (unconfigured) **or 4** (configured but unreachable — external drive not mounted / path gone) → call `AskUserQuestion` to ask the user for the document directory (absolute path, used **verbatim** as the specs root; specode makes no assumptions about its structure and appends nothing) → after the user provides it, persist with `set-root --root <abs>` → never ask again. For exit 4 specifically, first surface the unreachable path + likely cause (外置盘未挂载？) so the user can choose to remount and retry instead of overwriting the config; only `set-root` a new path if they provide one. `project_root` is **inferred per-spec** (default: `git rev-parse --show-toplevel` of cwd, falling back to cwd itself) and **confirmed once via `AskUserQuestion`** before requirements is written — see §requirements phase. Path-resolution details are in `references/obsidian.md`.

## Flow (start → coding complete)

Each phase is annotated "if superpowers is installed, call it / otherwise go native". To decide "installed or not": **first try to call the matching superpowers skill via the `Skill` tool; if it is unavailable (skill missing / call fails), take the native branch.**

1. **specsRoot**: `get-root` (first-time setup if missing) → obtain `<specsRoot>` → `mkdir -p <specsRoot>/<slug>/` (the host agent derives the kebab-case slug from the request).
2. **requirements (clarify + requirements)** — **invoke the `specode:intake` skill via the `Skill` tool** and let it own this whole phase. intake is a **standalone specode skill** (`skills/intake/`, peer to `distill`, `user-invocable: false`) — it is the **sole producer of `requirements.md`**; there is **no** "superpowers vs native" fork here anymore (`brainstorming` is used only for design, see step 3). intake internally runs, in order: (1) `project_root` confirmation (`resolve-project-root` default → `AskUserQuestion` once) — it holds the confirmed absolute path; (2) **project analysis**: agent-docs scan (`## 项目级约束` path-only section) + **experience retrieval — this is the primary retrieval node** (per `references/retrieval.md`: Tier-0 RagKit / two-tier gated) + actually reading the located real code; (3) analysis-driven clarification (brainstorming-caliber, one question at a time, not a fixed wizard); (4) write `requirements.md` per the template **and persist the frontmatter contract** — `spec_id` / `created_at` + `project_root` **via `resolve_root.py write-project-root`** (single validated writer; never hand-write it); (5) hand the located 「参考定位（非事实来源）」 pointers back as ephemeral context for design. Full behavior lives in `skills/intake/SKILL.md` — do not re-derive it here.

   > **frontmatter contract 🔒**: `requirements.md`'s `spec_id` / `created_at` / `project_root` are the single source of truth for downstream distill / task-swarm / retrieval; `project_root` is written only through the single writer `write-project-root`. intake guarantees this contract; the specode orchestration does not re-write or hand-edit it.
3. **design (traditional design doc)**:
   - superpowers installed → call `superpowers:brainstorming` for **design only** (single artifact → `design.md`). Pre-instruct it: **requirements are already settled in `requirements.md` (read it as input) — go straight to design presentation, produce only `design.md`** per the `assets/templates/design.md` sections (背景与目标 / 架构概览 / 模块划分与职责 / 接口设计 / 数据流 / 错误处理 / 测试策略 — prose, no checkboxes); also pass intake's 「参考定位（非事实来源）」 pointers as ephemeral grounding context. Relocate the artifact to `<specsRoot>/<slug>/design.md` (post-relocation check = **one** file).

     > brainstorming's terminal state is hardcoded to "invoke writing-plans" — that happens to align with specode's design → tasks order, so **let it flow naturally**: once design.md is produced (by it or by you), proceed into the tasks phase (step 4); don't start over inside design.
   - not installed → **specode-native**: the host agent authors `design.md` per the `assets/templates/design.md` template (same seven sections, prose, no checkboxes).
   - **experience retrieval (conditional top-up, not mandatory)**: design **inherits intake's (step 2) already-located pointers** by default and does not re-run a full retrieval. Only when design opens territory intake didn't cover, re-query once per `references/retrieval.md` (frontmatter is written by this phase, so get `project_root` via `resolve_root.py read-project-root --spec <specsRoot>/<slug>`); the hits' front/back-end files + call chains ground **module boundaries / interface design to real code** (design's judgment is still based on real code). `<project_root>/knowledge-base/MEMORY.md` absent → silently skip.

   > design retrieval is **for locating** (grounding the design to real code), producing pointers only and **introducing no "rule acknowledgement / deviation gate"** (since 4.0.0, no `.ai-memory/knowledge/rules/`-related rule check; don't reintroduce it).
4. **tasks (executable plan)**:
   - superpowers installed → call `superpowers:writing-plans`. Pre-instruct the target path `<specsRoot>/<slug>/tasks.md`. **writing-plans ends by hardcoding a "Subagent-Driven vs Inline Execution" question — it has no flag to disable it; ignore that question and don't act on it**, and continue to Flow step 5 (invoke `specode:execute`). specode can only "digest" that question, not truly suppress it.
   - not installed → **specode-native**: break down into `## Task N` + `**Files:**` + `**Interfaces:**` + `验证: AC-N` + `- [ ]` TDD steps per the `assets/templates/tasks.md` template.
   - Relocate the artifact to `<specsRoot>/<slug>/tasks.md`.
   - the tasks phase does **no separate retrieval** — it inherits the file paths already located in design.md (each `**Files:**` derives from design's module/interface landing points).
5. **Execution tail (selector → execution → acceptance)** — **invoke the `specode:execute` skill via the `Skill` tool** and let it own everything from here: the 「执行方式」 selector (verbatim per its own `references/selectors.md`), engine dispatch (task-swarm handoff / superpowers subagent-driven / executing-plans / specode self-execute, all TDD), `implementation-log.md` appending, acceptance, and the distill prompt. execute is a **standalone user-invocable skill** (`skills/execute/`, peer to intake/distill) — the user can also trigger it manually at any time as `/specode:execute <slug>` (e.g. after a session break or a `/specode:continue`). Full behavior lives in `skills/execute/SKILL.md` — do not re-derive it here.

phase ↔ skill quick map: `requirements` → **`specode:intake`** (specode's own standalone skill, always — no superpowers fork); `design` → brainstorming (design only, single artifact) or native; `tasks` → writing-plans; execution + acceptance → **`specode:execute`** (specode's own standalone user-invocable skill, which internally dispatches task-swarm / subagent-driven-development / executing-plans / native TDD, then verification-before-completion / native acceptance).

## superpowers orchestration + relocation (belt and suspenders)

superpowers' brainstorming / writing-plans have their own default output paths + filenames (e.g. `docs/superpowers/specs/YYYY-MM-DD-*.md`), so when delegating, specode must actively relocate to guarantee the core invariant holds. (Note: `requirements.md` is **not** produced by superpowers anymore — it is produced by the `specode:intake` skill, which writes directly to the fixed path, so no relocation is needed for it.)

1. **Pre-instruction**: before calling the skill, explicitly tell it the target **absolute path + fixed filename** (superpowers' spec/plan locations support user-preference overrides) — brainstorming → **one** target: `<specsRoot>/<slug>/design.md` (design only; requirements are already in `requirements.md`); writing-plans' plan output → `<specsRoot>/<slug>/tasks.md` (the tasks format *is* the writing-plans format, so it slots in seamlessly). writing-plans will still end by asking its own execution-handoff question — **ignore it, don't act on it**; the 执行方式 selector presented by `specode:execute` supersedes it.
2. **Post-relocation (backstop)**: after the skill returns, verify the expected `<specsRoot>/<slug>/<fixed-name>` is in place (brainstorming: `design.md`; writing-plans: `tasks.md`); if not, `mv` / rename the file the skill actually produced to the fixed location. The invariant holds whether or not the skill honored the pre-instruction.

Which superpowers skill to call when, and how to do pre/post, is detailed in `references/superpowers-wiring.md`.

## Absence fallback (first-class, not a footnote)

specode treats both superpowers and task-swarm as **soft dependencies** (purely runtime, invoked via this SKILL's prose, zero imports). When absent, planning / execution / acceptance **all sink down to specode itself**, guaranteeing a full start → coding-complete run with only specode installed — the native path is **first-class**, not a footnote. (requirements is never a fallback case: it always runs through `specode:intake`, which is specode-native by design.) The per-phase producer ↔ superpowers-skill ↔ native-fallback table lives in `references/superpowers-wiring.md`; the native branches are also spelled out inline per phase in §Flow above.

**How to decide**: requirements always goes through `specode:intake` (no superpowers here). For design / tasks / execution / acceptance, the host agent first tries calling the matching superpowers skill via `Skill`; if unavailable, take the native branch. Do not stall or tell the user to install something just because superpowers is absent — pick up natively right away.

## Execution tail → `specode:execute`

The 「执行方式」 selector, the engine dispatch, the task-swarm handoff, acceptance, and the distill prompt all live in the sibling **`specode:execute`** skill (`skills/execute/SKILL.md`) — invoked by this pipeline at Flow step 5, by `/specode:continue` on resume, or manually by the user as `/specode:execute <slug>`. This SKILL intentionally carries none of that content; never re-derive the selector or the handoff here.

## Output Language

User-facing output (summaries, questions, confirmations, status, errors) must be in **Chinese (中文)**.

Keep in English / verbatim: technical names, commands, file paths, code identifiers; the contents of code blocks; this skill's own rule files (SKILL.md / references). If the request is in English, the generated spec documents may be in English; other user-facing summaries / confirmations remain in Chinese.

## Document output brevity

When writing / updating spec documents, **never** reprint the full text in chat. A report contains only: the file path (one line) + 3-8 section-title or key-change bullets + open questions (if any) + the next action. Never paste document body, full Task lists, or design rationale. The only exception is when the user explicitly asks.

## Iron rules

1. **Fixed-artifact invariant**: always produce only the 4 documents `requirements.md` / `design.md` / `tasks.md` / `implementation-log.md`, with fixed filenames, filed in `<specsRoot>/<slug>/`, independent of the execution engine. `requirements.md` is written directly by the `specode:intake` skill (no relocation); after delegating design/tasks to superpowers you must run the post-relocation check (brainstorming → `design.md`; writing-plans → `tasks.md`).
2. **specsRoot: read config first, then ask**: call `get-root` on every start; only when missing, `AskUserQuestion` once and `set-root` to write it back, then use it silently thereafter; use the user's directory verbatim as the root, appending nothing.
3. **CLIs must go through run.sh via a relative path**: all specode CLIs go through the `run.sh` wrapper called as `../../scripts/run.sh ../../scripts/<name>.py` (paths relative to this skill's base directory, superpowers-style — no env-var resolution, no cache `find`); never a bare `python3 <script>`, never a hard-coded version path.
4. **Execution tail goes through `specode:execute`**: after tasks.md is confirmed, always invoke the `specode:execute` skill via the `Skill` tool — never present the 执行方式 selector or dispatch engines from this SKILL's own prose (the verbatim selector example lives in `skills/execute/references/selectors.md`).
5. **Lightweight red line**: no more locking / takeover protocol / state machine; no more status-summary footer line; no more forced code-doc sync nagging; no more paired writes of a persistent session file and spec config file; no more pending-selector markers / phase-transition CLI / log collection. Active state is inferred from the current conversation context + document existence.

## References

- `../intake/SKILL.md` — the standalone `specode:intake` skill: full behavior of the requirements phase (project analysis + experience retrieval + clarification + writing `requirements.md` with the frontmatter contract). Invoked via the `Skill` tool at Flow step 2.
- `../execute/SKILL.md` — the standalone `specode:execute` skill: full behavior of the execution tail (执行方式 selector + engine dispatch + task-swarm handoff + acceptance + distill prompt). Invoked via the `Skill` tool at Flow step 5; also user-invocable as `/specode:execute <slug>`.
- `references/selectors.md` — verbatim `AskUserQuestion` example for the first-time directory-setup question (the 执行方式 selector example moved to `../execute/references/selectors.md` in 6.3.0).
- `references/obsidian.md` — specsRoot path resolution, the full `resolve_root.py` verb table, and directory conventions.
- `references/superpowers-wiring.md` — the per-phase ↔ superpowers skill mapping, pre-instructions, and post-relocation instructions.
- `references/retrieval.md` — experience-retrieval injection spec (intake project-analysis is the primary node / design is a conditional top-up).
- `references/knowledge-flow.md` — one-page knowledge-loop mental model: who produces / indexes / reads distill / knowledge-base / MEMORY / ragkit / intake-retrieval, and when.
