---
name: intake
user-invocable: false
description: Use when running specode's requirements phase — project analysis + code location + clarification, then writing requirements.md. Produces <specsRoot>/<slug>/requirements.md (with the project_root frontmatter contract) plus the location pointers handed to the design phase. Invoked by name (specode:intake) via the Skill tool by the specode orchestration SKILL; not a user-triggered command.
---

# intake — specode's requirements-intake engine

## §0 Who you are / when you're invoked

- The specode orchestration shell invokes you by name (`specode:intake`) via the `Skill` tool during the **requirements phase**. By then `<specsRoot>` is resolved, `<specsRoot>/<slug>/` exists, and the slug is fixed.
- You are the **sole producer of `requirements.md`** — specode no longer forks the requirements phase on "superpowers present or not". superpowers' `brainstorming` is used only for **design** from here on; it never moonlights as a requirements writer.
- What sets you apart from the old "native 2-4 question wizard" is entirely **§Step 2 project analysis** + **§Step 3 analysis-driven clarification**: read the real project first to establish a factual baseline, then ask grounded questions — that is specode's own "driving capability", not a blank questionnaire.
- Your outputs:
  1. `<specsRoot>/<slug>/requirements.md` — prose requirements plus the hard frontmatter contract (§1);
  2. a block of **`参考定位（非事实来源）`** location pointers handed to the design phase (§5, ephemeral context, never persisted as fact).

## §1 Hard constraints 🔒 (never violate)

1. **Frontmatter contract (highest priority — explicitly required by the user)**: the YAML at the top of `requirements.md` **must** carry three fields — `spec_id` / `created_at` / `project_root`. `project_root` is the **single source of truth** for downstream distill / task-swarm / retrieval, and it may **only** be written through the single validated writer `resolve_root.py write-project-root` (it validates absolute path / dir exists / `/Volumes` mount); **never hand-write that field**. You change *who generates the body of requirements*, and must **never** break these contract elements.
2. **Prose requirements**: `requirements.md` is a natural-language spec (background / scope in-out / `- [ ] AC-N` / open questions), **no formalized clauses, no checkboxes** — the plan lives in tasks.md and the design in design.md; don't cross that boundary. Bug fixes go here as Current / Expected prose; there is no separate `bugfix.md`.
3. **User-facing output is Chinese** — technical names / paths / code identifiers / frontmatter key names stay verbatim.
4. **Never reprint the full document** (see §5 reporting discipline).

## §2 run.sh resolver prefix (every CLI call)

Every `resolve_root.py` call **must** go through the `run.sh` wrapper. The scripts live in the plugin's `scripts/` directory — relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an absolute one (do **not** resolve env vars, do **not** `find` the cache):

```bash
sh ../../scripts/run.sh ../../scripts/resolve_root.py <verb> <args...>
```

## §3 Autonomous-mode awareness (applies at every AskUserQuestion site)

This skill has two `AskUserQuestion` sites (§Step 1 project_root confirmation, §Step 3 clarification). At each, first apply the autonomous-mode rule to decide whether to skip — the full rule (gate→key→env mapping + decision pseudo-code) is in `skills/spec/references/autonomous-mode.md`. In short: when `interactive == false` and the gate's key has `source ∈ {env, file}`, skip the prompt and use the default; otherwise ask via `AskUserQuestion`. This skill's two gates: project_root confirmation → key `project_root_default`; clarification → no dedicated key, governed only by the `interactive` master switch (when non-interactive, draft from the information at hand and record uncertainties under "开放问题" instead of blocking).

## §4 Flow (5 steps; quality is in Step 2–3)

### Step 1 — Confirm project_root (required, autonomous-aware)

1. Get the default: `resolve_root.py resolve-project-root` (returns `git rev-parse --show-toplevel` of cwd, else cwd).
2. Decide per §3: `AskUserQuestion` once (default pre-selected, user confirms or overrides), or use the default directly in autonomous mode.
3. **Hold the confirmed absolute path** — Step 2 (constraint scan + retrieval) uses it, and Step 4 persists it via `write-project-root`. At this point requirements.md frontmatter is not yet written, so use the held absolute path directly; do **not** call `read-project-root`.

### Step 2 — Project analysis (what lifts intake above a questionnaire — read the real project before asking)

Don't stop at "ask the user what they want" — **read the real project first to build a factual baseline**:

- **a. Project-level constraint scan** (filesystem-only): scan the following existing files and inject them **path-only** (do not copy content) into the requirements draft as a `## 项目级约束（CLAUDE.md / AGENT.md）` section. Scan order (deduped, existing only): (1) `<project_root>/CLAUDE.md|AGENTS.md|AGENT.md|CODEBUDDY.md`; (2) the same four files in `<project_root>`'s immediate parent (covers a monorepo workspace root); (3) any subdirectory named in the user's request. Section template:

  ```markdown
  ## 项目级约束（CLAUDE.md / AGENT.md）

  > 主 agent 的 system prompt 已自动加载下列文件；这里列出来是为了 design / 执行阶段 / 下游 task-swarm subagent 都能看见这条约束链路。**优先级高于本 spec 的其他描述**：冲突时以下列文件为准。

  - `<abs/path/to/CLAUDE.md>`
  - `<abs/path/to/parent/AGENTS.md>`
  ```

  Why path-only: the main agent already has the full content in context, so copying it in is redundant + staleness risk; task-swarm renders task.md by injecting these paths into subagent prompts by the same rule. If nothing is found (a typical fresh project) → **omit the whole section** (don't write a "none" placeholder).

- **b. Experience-retrieval location** (when `<project_root>/knowledge-base/MEMORY.md` exists) — **this is the primary node for ragkit / experience retrieval**. Run it per `skills/spec/references/retrieval.md`: try the Tier-0 gate first (`ragkit:query` multi-recall when ragkit is available and `knowledge-base/.ragkit/chunks.json` exists), otherwise the two-tier gated flow (Tier-1 reads the small MEMORY index and matches the current need's page/field/domain; on a hit, Tier-2 reads ≤5 full docs). Produce `参考定位（非事实来源）` pointers (file paths + call chains). MEMORY.md absent → **silently skip** (no error, no empty section). **Top-level invariant**: pointers only locate real code; **real code is the only source of truth** — never treat KB content as the truth about current code.

- **c. Read the real code**: for the key files located in (b), **actually open and read them** (not just collect paths) — understand the existing structure / naming / patterns as the factual baseline for requirements analysis and scoping.

- **d. Fresh project** (no knowledge-base, no agent docs) → (b)/(c) silently skipped; build understanding from Step 3 clarification + the user's description.

### Step 3 — Clarification (brainstorming-caliber, not a fixed questionnaire)

On top of Step 2's project analysis, **clarify one question at a time** (prefer multiple-choice), covering **purpose / scope (in / out) / constraints / success criteria**. The key: **let Step 2's analysis drive the questions** — ask grounded questions like "given the existing `X` code/pattern, how should this requirement plug in / where's the boundary" rather than a blank questionnaire.

- Autonomous-aware (§3): when non-interactive, draft from what you have and record uncertainties under "开放问题" instead of blocking.
- **When to stop**: once intent / scope / AC are clear enough and open questions are listed — don't over-ask (YAGNI).

### Step 4 — Write requirements.md

Write the body per `assets/templates/requirements.md`: `## 背景 / 为什么` · `## 范围` (in / out) · `## 验收标准` (`- [ ] AC-N`, observable and verifiable) · `## 开放问题` (plus the `## 项目级约束` section from Step 2a, if any). Land it at `<specsRoot>/<slug>/requirements.md`.

Then persist the **frontmatter (§1 hard constraint)**:

1. Write `spec_id: <slug>` / `created_at: YYYY-MM-DD` (fine to write into the top YAML alongside the body).
2. **`project_root` is written only through the single writer**:
   ```bash
   sh ../../scripts/run.sh ../../scripts/resolve_root.py write-project-root --spec <specsRoot>/<slug> --root <confirmed abs path from Step 1>
   ```
   It validates and writes `project_root` into requirements.md frontmatter. **Never hand-write that field.**

### Step 5 — Hand off to design

Hand Step 2b's `参考定位（非事实来源）` pointers back to the specode orchestration as **ephemeral context** for the design phase (specode passes them as context when it calls `brainstorming`, or native design reuses them directly). **Do not persist them as factual conclusions in requirements.md** (the retrieval.md top-level invariant). Design inherits these pointers by default and only re-queries when it opens new territory intake didn't cover (design's retrieval is a **conditional top-up**, not mandatory).

After the handoff, **end this skill** and return control to the specode orchestration (which proceeds into the design phase).

## §5 Reporting discipline

Don't reprint the full requirements.md. Report only: the file path (one line) + 3-8 key points / clarifications + open questions (if any) + the next action (entering design). The only exception is when the user explicitly asks for the full text.

## §6 References

- `skills/spec/references/retrieval.md` — experience-retrieval spec (the engine behind Step 2b; intake is its **primary node**).
- `assets/templates/requirements.md` — requirements template (Step 4 structure + frontmatter contract).
- `skills/spec/references/autonomous-mode.md` — the full rule behind §3 (gate→key→env + pseudo-code).
- `skills/spec/references/knowledge-flow.md` — one-page knowledge-loop mental model (the global picture of who writes/reads the KB and when).
