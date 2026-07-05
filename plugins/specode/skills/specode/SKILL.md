---
name: specode
user-invocable: false
description: Lightweight spec-driven workflow orchestration shell. Across the requirements → design → tasks → 「执行方式」 → execute → acceptance phases it autonomously calls mature superpowers skills to do the heavy lifting (clarification, design, planning, TDD execution, acceptance), falling back to specode-native when superpowers is absent, and files the four fixed artifacts (requirements.md / design.md / tasks.md / implementation-log.md) into the user's document directory. Activates only when the user invokes `/specode:spec <request>`, `/specode:continue <slug>`, `/specode:list`, or explicitly asks to enter spec mode; otherwise behave as a normal conversation.
---

# specode — orchestration shell

specode is no longer a state machine. It is an **orchestration shell** that handles only its own distinctive value: the spec lifecycle, fixed on-disk artifacts, "documents-as-state" phase inference, the `执行方式` selector, and the task-swarm handoff bridge. The heavy lifting (clarification, design, TDD execution, acceptance) is done by **autonomously calling superpowers** skills in the matching phase; when superpowers is absent, **specode-native fallback** takes over. There is no persistent session file, no multi-window locking, no spec config file, no status-summary footer line, no forced code-doc sync nagging, and no session log collection.

## Activation Guard

Activate only in one of these cases:

- The current user input is `/specode:spec <request>`, `/specode:continue <slug>`, or `/specode:list`.
- The user explicitly says "use spec mode" / "按 spec 流程做" / equivalent.

Otherwise **do not activate**; handle as normal conversation. There is **no session file** — whether a spec is active is inferred entirely from the **current conversation context** (which slug is running this turn) plus the **documents under `<specsRoot>/<slug>/`**. No persistent state file is ever read.

## Core invariant 🔒

Regardless of the execution engine (superpowers, task-swarm, or specode-native), a spec's artifacts are **always** the 4 documents below, with **fixed filenames**, **filed in a fixed location** at `<specsRoot>/<slug>/`. The engine only decides *who generates the content*; it never changes the artifacts' shape, naming, or location.

| Document | Fixed filename | Content |
|---|---|---|
| Requirements | `requirements.md` | Prose spec: background / why · scope (in/out) · acceptance `- [ ] AC-N` · open questions. Pure natural language, no formalized clause syntax. |
| Design | `design.md` | **传统设计文档** (per the `assets/templates/design.md` sections): 背景与目标 / 架构概览（方案取舍）/ 模块划分与职责 / 接口设计 / 数据流 / 错误处理 / 测试策略. Prose + diagrams only — no checkboxes, no TDD steps. |
| Plan | `tasks.md` | superpowers writing-plans executable-plan format: `Goal` / `Architecture` / `Tech Stack` + `## Task N` (each Task carries `**Files:**` file scope, `**Interfaces:**` Consumes/Produces contracts, `验证: AC-N` back-reference to requirements, `(needs: Task N)` dependencies, and `- [ ]` TDD steps). Engine-neutral — all four execution engines consume this one file. |
| Execution log | `implementation-log.md` | Appended during execution: design deviations / key decisions / final acceptance summary. |

Bug fixes do not get a separate `bugfix.md` — write Current / Expected directly in `requirements.md` as prose. `pipeline.yml` is generated only temporarily when delegating to task-swarm; it is not a fixed artifact.

## specsRoot resolution (read on every start; ask only once if missing)

**Every time specode starts, first call `resolve_root.py get-root` via run.sh to read specsRoot.** Only when the config is missing (typically first use) ask the user via `AskUserQuestion`, then immediately `set-root` to write it back to config. Afterwards all sessions use it silently and automatically, never prompting again.

All specode CLIs **must** be invoked through the `run.sh` wrapper with an **absolute** plugin-root path — the host env var `$CLAUDE_PLUGIN_ROOT` (CodeBuddy: `$CODEBUDDY_PLUGIN_ROOT`) is **not** reliably set in skill-driven Bash, so always fall back to a cache `find`, and never call a bare `python3 <script>`. Shell state does not persist between Bash calls, so prefix **every** CLI call with this self-contained resolver:

```bash
R="${CLAUDE_PLUGIN_ROOT:-$CODEBUDDY_PLUGIN_ROOT}"; [ -f "$R/scripts/run.sh" ] || R="$(find "$HOME/.claude/plugins/cache" "$HOME/.codebuddy/plugins/cache" -path '*/specode/*/scripts/run.sh' 2>/dev/null | sort -V | tail -1)"; R="${R%/scripts/run.sh}"
sh "$R/scripts/run.sh" "$R/scripts/resolve_root.py" <verb> <args...>
```

(`find` not a shell glob — zsh aborts on an unmatched glob; `find` stays silent. `sort -V | tail -1` picks the newest cached version, never hard-coded. `run.sh` probes `python3 → python → py`.) The full **verb table** (`get-root` / `set-root` / `list-specs` / `resolve|write|read-project-root` / `plan-unchecked` / `read|write|reset-default`) lives in `references/obsidian.md`.

**Autonomous-mode defaults rule 🔒**: at every `AskUserQuestion` gate below, first read the relevant default + source via `read-defaults --key <relevant> --json`; when `interactive == false` **and** `source ∈ {env, file}`, skip the prompt and use the default (autonomous / CI path); `interactive == true` → all gates behave as before (zero behavior change). The gate→key→env mapping and the decision pseudo-code live in `references/autonomous-mode.md`.

**project_root single-source-of-truth rule 🔒**: project_root lives in exactly one place — the spec's `requirements.md` frontmatter. The `specode:intake` skill writes it once (via `write-project-root`); every later phase and downstream skill (distill, task-swarm) obtains it via `read-project-root`. No component re-derives it from cwd / workdir / guessing.

**First-time setup flow**: `get-root` exits 3 → call `AskUserQuestion` to ask the user for the document directory (absolute path, used **verbatim** as the specs root; specode makes no assumptions about its structure and appends nothing) → after the user provides it, persist with `set-root --root <abs>` → never ask again. `project_root` is **inferred per-spec** (default: `git rev-parse --show-toplevel` of cwd, falling back to cwd itself) and **confirmed once via `AskUserQuestion`** before requirements is written — see §requirements phase. Path-resolution details are in `references/obsidian.md`.

## Flow (start → coding complete)

Each phase is annotated "if superpowers is installed, call it / otherwise go native". To decide "installed or not": **first try to call the matching superpowers skill via the `Skill` tool; if it is unavailable (skill missing / call fails), take the native branch.**

1. **specsRoot**: `get-root` (first-time setup if missing) → obtain `<specsRoot>` → `mkdir -p <specsRoot>/<slug>/` (the host agent derives the kebab-case slug from the request).
2. **requirements (clarify + requirements)** — **invoke the `specode:intake` skill via the `Skill` tool** and let it own this whole phase. intake is a **standalone specode skill** (`skills/intake/`, peer to `distill`, `user-invocable: false`) — it is the **sole producer of `requirements.md`**; there is **no** "superpowers vs native" fork here anymore (`brainstorming` is used only for design, see step 3). intake internally runs, in order: (1) `project_root` confirmation (`resolve-project-root` default → `AskUserQuestion` once, autonomous-aware) — it holds the confirmed absolute path; (2) **project analysis**: agent-docs scan (`## 项目级约束` path-only section) + **experience retrieval — this is the primary retrieval node** (per `references/retrieval.md`: Tier-0 RagKit / two-tier gated) + actually reading the located real code; (3) analysis-driven clarification (brainstorming-caliber, one question at a time, not a fixed wizard); (4) write `requirements.md` per the template **and persist the frontmatter contract** — `spec_id` / `created_at` + `project_root` **via `resolve_root.py write-project-root`** (single validated writer; never hand-write it); (5) hand the located 「参考定位（非事实来源）」 pointers back as ephemeral context for design. Full behavior lives in `skills/intake/SKILL.md` — do not re-derive it here.

   > **frontmatter 契约 🔒**: `requirements.md` 的 `spec_id` / `created_at` / `project_root` 是下游 distill / task-swarm / retrieval 的单一事实源；`project_root` 只经 `write-project-root` 单一写入口落盘。intake 负责保证这套契约，specode 编排不重复写、不手改。
3. **design (传统设计文档)**:
   - superpowers installed → call `superpowers:brainstorming` for **design only** (single artifact → `design.md`). Pre-instruct it: **requirements are already settled in `requirements.md` (read it as input) — go straight to design presentation, produce only `design.md`** per the `assets/templates/design.md` sections (背景与目标 / 架构概览 / 模块划分与职责 / 接口设计 / 数据流 / 错误处理 / 测试策略——散文，无 checkbox); also pass intake's 「参考定位（非事实来源）」 pointers as ephemeral grounding context. Relocate the artifact to `<specsRoot>/<slug>/design.md` (post-relocation check = **one** file).

     > brainstorming 的终态硬编码为「invoke writing-plans」——这正好对齐 specode 的 design → tasks 顺序，**顺其自然即可**：让它（或你）产完 design.md 后进入 tasks phase（step 4），不要在 design 里另起炉灶。
   - not installed → **specode-native**: the host agent authors `design.md` per the `assets/templates/design.md` template（同上七节，散文无 checkbox）.
   - **经验检索（条件性 top-up，非强制）**: design 默认**继承 intake（step 2）已定位的指针**，不重复全量检索。仅当 design 开辟了 intake 未覆盖的新领域时，才按 `references/retrieval.md` 补查一次（此 phase frontmatter 已写，用 `resolve_root.py read-project-root --spec <specsRoot>/<slug>` 取 `project_root`）；命中点的前后端文件 + 调用链用于把**模块边界 / 接口设计 ground 到真实代码**（design 的判断仍基于真实代码）。`<project_root>/knowledge-base/MEMORY.md` 不存在 → 静默跳过。

   > design 检索是**定位用**（把设计 ground 到真实代码），只产出指针、**不引入任何「规则确认 / 偏离 gate」**（4.0.0 起不做任何 `.ai-memory/knowledge/rules/` 关联的 rule 检查；勿重新引入）。
4. **tasks (executable plan)**:
   - superpowers installed → call `superpowers:writing-plans`. Pre-instruct the target path `<specsRoot>/<slug>/tasks.md`. **writing-plans 结尾会硬编码问一句「Subagent-Driven vs Inline Execution」——它无参数可关；忽略那个提问、不据此进入执行**，继续走 specode 自己的 §执行方式 selector（step 5）。specode 只能"消化"这个提问，不是真的能抑制它。
   - not installed → **specode-native**: break down into `## Task N` + `**Files:**` + `**Interfaces:**` + `验证: AC-N` + `- [ ]` TDD steps per the `assets/templates/tasks.md` template.
   - Relocate the artifact to `<specsRoot>/<slug>/tasks.md`.
   - tasks 阶段**不做单独检索**——直接继承 design.md 已定位好的文件路径（`**Files:**` 从 design 的模块/接口落点导出）。
5. **「执行方式」selector**: after tasks.md is confirmed, call `AskUserQuestion` to present it (adaptive 4 options, see §执行方式 selector), verbatim per the `references/selectors.md` example.
6. **Execution** (branches by selector choice, all TDD):
   - Delegate to task-swarm (installed) → see §task-swarm handoff.
   - superpowers subagent-driven (installed) → call `superpowers:subagent-driven-development`.
   - superpowers executing-plans (installed) → call `superpowers:executing-plans`.
   - specode self-execute (fallback) → the host agent runs TDD in `tasks.md` Task order (write failing test → run red → implement → run green), checking off each `- [ ]`.
   - Append to `implementation-log.md` during execution.
7. **Acceptance (coding complete)**:
   - superpowers installed → call `superpowers:verification-before-completion` (optionally also `superpowers:requesting-code-review`).
   - not installed → **specode-native**: the host agent verifies item by item against the `AC-N` in `requirements.md` / `design.md` 测试策略 / `tasks.md` checkbox 全勾.
   - Say "请验收" in prose and write an acceptance summary in `implementation-log.md`. **There is no formal acceptance-gate selector.**
   - **沉淀提示（distill, gated by `auto_distill`）**: acceptance 写完后，按 §Autonomous-mode defaults rule 决定是否提示沉淀 —— 用 §specsRoot resolver `resolve_root.py read-defaults --key auto_distill --json` 取 effective value + source；当 `interactive == false` 且有 effective default（`source ∈ {env, file}`）时按 default **静默处理**（不打断），否则 `AskUserQuestion`「是否运行 `/specode:distill <slug>` 把本次经验沉淀进项目 knowledge-base？」。distill 仍是**用户触发的独立命令**（本体行为见 `skills/distill/SKILL.md`，Plan A 已改为项目 `knowledge-base/` primary）；这里只把入口提示重新挂回 acceptance 末尾，**不在主流程里自动跑 distill**。

   > **v4.0.0 → 重新挂回**: 4.0.0 曾把 acceptance 后的自动 distill sub-step 整体移除；现按 `auto_distill` default **把入口提示重新挂回**（见上一条 bullet，遵循既有 autonomous-mode 规则——interactive 时询问、非 interactive 有 effective default 时静默，**非无条件自动执行**）。沉淀目标是项目 `knowledge-base/`（供下次 requirements/design 检索定位），md-only 行为见 `skills/distill/SKILL.md`。

phase ↔ skill quick map: `requirements` → **`specode:intake`** (specode's own standalone skill, always — no superpowers fork); `design` → brainstorming (design only, single artifact) or native; `tasks` → writing-plans; execution → subagent-driven-development / executing-plans (the task-swarm path does not use superpowers); acceptance → verification-before-completion / requesting-code-review.

## superpowers orchestration + relocation (belt and suspenders)

superpowers' brainstorming / writing-plans have their own default output paths + filenames (e.g. `docs/superpowers/specs/YYYY-MM-DD-*.md`), so when delegating, specode must actively relocate to guarantee the core invariant holds. (Note: `requirements.md` is **not** produced by superpowers anymore — it is produced by the `specode:intake` skill, which writes directly to the fixed path, so no relocation is needed for it.)

1. **Pre-instruction**: before calling the skill, explicitly tell it the target **absolute path + fixed filename** (superpowers' spec/plan locations support user-preference overrides) — brainstorming → **one** target: `<specsRoot>/<slug>/design.md` (design only; requirements are already in `requirements.md`); writing-plans' plan output → `<specsRoot>/<slug>/tasks.md` (the tasks format *is* the writing-plans format, so it slots in seamlessly). writing-plans will still end by asking its own execution-handoff question — **ignore it, don't act on it**; specode's 执行方式 selector supersedes it.
2. **Post-relocation (backstop)**: after the skill returns, verify the expected `<specsRoot>/<slug>/<fixed-name>` is in place (brainstorming: `design.md`; writing-plans: `tasks.md`); if not, `mv` / rename the file the skill actually produced to the fixed location. The invariant holds whether or not the skill honored the pre-instruction.

Which superpowers skill to call when, and how to do pre/post, is detailed in `references/superpowers-wiring.md`.

## Absence fallback (first-class, not a footnote)

specode treats both superpowers and task-swarm as **soft dependencies** (purely runtime, invoked via this SKILL's prose, zero imports). When absent, planning / execution / acceptance **all sink down to specode itself**, guaranteeing a full start → coding-complete run with only specode installed — the native path is **first-class**, not a footnote. (requirements is never a fallback case: it always runs through `specode:intake`, which is specode-native by design.) The per-phase producer ↔ superpowers-skill ↔ native-fallback table lives in `references/superpowers-wiring.md`; the native branches are also spelled out inline per phase in §Flow above.

**How to decide**: requirements always goes through `specode:intake` (no superpowers here). For design / tasks / execution / acceptance, the host agent first tries calling the matching superpowers skill via `Skill`; if unavailable, take the native branch. Do not stall or tell the user to install something just because superpowers is absent — pick up natively right away.

## 执行方式 selector (the single fixed per-spec selector, after tasks.md completes)

After tasks.md is confirmed, call `AskUserQuestion` to present **adaptive 4 options** — **show an option only if its engine is installed**:

1. **委托 task-swarm（多 agent 并发）** — requires task-swarm.
2. **superpowers subagent-driven（每 Task 派全新 subagent + 两阶段评审，推荐）** — requires superpowers.
3. **superpowers executing-plans（当前会话顺序批量 + checkpoint）** — requires superpowers.
4. **specode 自执行（顺序单 agent）** — native fallback, the only option when nothing is installed.

> Options 2/3 are both superpowers skills (built on Claude Code's native Agent/subagent capabilities), not Claude built-in workflows; their ergonomics differ (the former: clean context + per-Task review; the latter: single-session continuous batch).

When presenting, pass question / header / options **verbatim** per the `references/selectors.md` example — do not invent and do not collapse into a shorter option set. This is a single-user scenario with the PreToolUse hard-check removed, so "verbatim per the example" is enforced by this rule alone.

## Continuation (documents-as-state)

`/specode:continue <slug>` (slug required; missing or nonexistent → error + suggest `/specode:list` first): locate `<specsRoot>/<slug>/`, read the directory contents, and infer the phase per this table.

**加载即停（load-and-stop）🔒**: `/specode:continue <slug>` never auto-resumes. It does exactly three things: (1) locate `<specsRoot>/<slug>/` and read every fixed doc present; (2) report a **progress brief** — slug, inferred phase, per-doc existence, tasks.md checkbox progress (x/N; legacy specs: design.md checkboxes), and what the next action *would* be; (3) **stop and wait for the user's instruction**. Only when the user says 继续 (or equivalent) does execution resume from the inferred phase; if the user instead supplies requirement changes, digest them into the affected docs first, then ask whether to resume. The "Resume action" column below describes what happens *after* the user gives the go-ahead — it is not automatic behavior.

| Directory state | Inferred phase | Resume action (after user go-ahead) |
|---|---|---|
| no `requirements.md` | intake | rerun requirements (brainstorming / native clarification) |
| has `requirements.md`, no `design.md` | design | run design (brainstorming design-only / native authoring) |
| has `design.md`, no `tasks.md`, and `design.md` contains `## Task` + `- [ ]` | **legacy spec (5.x)** | treat `design.md` as the plan per pre-6.0.0 semantics — resume execution / acceptance directly |
| has `design.md` (new-style, prose), no `tasks.md` | tasks | run tasks breakdown (writing-plans / native per tasks template) |
| `tasks.md` with unchecked `- [ ]` | executing | resume execution (task-swarm checks run state / superpowers resumes executing-plans / native resumes sequentially) |
| all `tasks.md` checkboxes checked | complete | run acceptance / report already complete |

`/specode:list` lists every spec under `<specsRoot>` with each one's inferred phase (for looking up slugs / overview; **does not resume**); if there are no specs → suggest `/specode:spec <request>` first.

## task-swarm handoff (zero hard dependency)

task-swarm is a **standalone plugin**; specode has **zero imports** of it and does not know its install path — all calls go through task-swarm's own `/task-swarm:swarm` command (which self-resolves its `$CLAUDE_PLUGIN_ROOT`). After the user picks "delegate":

1. Read this spec's `tasks.md` Task list + each Task's `**Files:**` + `(needs:)` → mechanically derive `<specsRoot>/<slug>/pipeline.yml` (merge Tasks into task groups by writes-conflict + needs topology / `@writes` files / `needs` topology).
2. **Show the yml summary to the user** (number of task groups / same-file conflicts / topology); init only after the user confirms.
3. Invoke task-swarm's own `/task-swarm:swarm` command to drive its plan → fork → advance → writeback → resolve orchestration until done.
4. Append to `implementation-log.md` throughout; run acceptance after done.

**task-swarm not installed** (`/task-swarm:swarm` unavailable) → fall back on the spot to "specode self-execute" or the superpowers execution path, so the user is never stuck.

## Output Language

User-facing output (summaries, questions, confirmations, status, errors) must be in **Chinese (中文)**.

Keep in English / verbatim: technical names, commands, file paths, code identifiers; the contents of code blocks; this skill's own rule files (SKILL.md / references). If the request is in English, the generated spec documents may be in English; other user-facing summaries / confirmations remain in Chinese.

## Document output brevity

When writing / updating spec documents, **never** reprint the full text in chat. A report contains only: the file path (one line) + 3-8 section-title or key-change bullets + open questions (if any) + the next action. Never paste document body, full Task lists, or design rationale. The only exception is when the user explicitly asks.

## Iron rules

1. **Fixed-artifact invariant**: always produce only the 4 documents `requirements.md` / `design.md` / `tasks.md` / `implementation-log.md`, with fixed filenames, filed in `<specsRoot>/<slug>/`, independent of the execution engine. `requirements.md` is written directly by the `specode:intake` skill (no relocation); after delegating design/tasks to superpowers you must run the post-relocation check (brainstorming → `design.md`; writing-plans → `tasks.md`).
2. **specsRoot: read config first, then ask**: call `get-root` on every start; only when missing, `AskUserQuestion` once and `set-root` to write it back, then use it silently thereafter; use the user's directory verbatim as the root, appending nothing.
3. **CLIs must go through run.sh + absolute path**: all specode CLIs go through the `run.sh` wrapper + an absolute plugin-root path resolved by the §specsRoot resolver (env var `$CLAUDE_PLUGIN_ROOT` / `$CODEBUDDY_PLUGIN_ROOT`, falling back to a cache glob — the env var is **not** reliably set in skill-driven Bash calls); never a bare `python3 <script>`, never a hard-coded version path.
4. **执行方式 selector verbatim per example**: the `AskUserQuestion` question / header / options are taken verbatim from `references/selectors.md`, adaptively showing only options for installed engines; never invent / collapse.
5. **Lightweight red line**: no more locking / takeover protocol / state machine; no more status-summary footer line; no more forced code-doc sync nagging; no more paired writes of a persistent session file and spec config file; no more pending-selector markers / phase-transition CLI / log collection. Active state is inferred from the current conversation context + document existence.

## References

- `../intake/SKILL.md` — the standalone `specode:intake` skill: full behavior of the requirements phase (project analysis + experience retrieval + clarification + writing `requirements.md` with the frontmatter contract). Invoked via the `Skill` tool at Flow step 2.
- `references/selectors.md` — verbatim `AskUserQuestion` example for the 「执行方式」 selector (the first-time directory-setup question is here too).
- `references/obsidian.md` — specsRoot path resolution, the full `resolve_root.py` verb table, and directory conventions.
- `references/autonomous-mode.md` — the autonomous / CI defaults rule: gate→key→env mapping + the skip-the-prompt decision pseudo-code.
- `references/superpowers-wiring.md` — the per-phase ↔ superpowers skill mapping, pre-instructions, and post-relocation instructions.
- `references/retrieval.md` — 经验检索注入规格（intake 项目分析为主节点 / design 条件性 top-up）。
