---
name: execute
description: Use when running a spec's execution tail — presents the 执行方式 selector, dispatches the chosen engine (task-swarm / superpowers / specode-native TDD), then runs acceptance and the distill prompt. Trigger /specode:execute <slug> manually at any time once tasks.md exists, or invoked by name (specode:execute) via the Skill tool by the spec / continue skills.
---

# /specode:execute — run a spec's execution tail (selector → execution → acceptance)

> **Host-tool convention** 🔧: tool names in this skill — `AskUserQuestion` (structured multiple-choice question), the `Skill` tool (invoke another skill by name), `Agent`/`Task` (dispatch a subagent) — are written for Claude-family hosts (Claude Code / CodeBuddy), where naming them directly is the most reliable. On a host that lacks one, use its nearest equivalent (a structured-question tool / a skill-invocation mechanism / a subagent-dispatch tool); with no equivalent, fall back to plain-text prose / reading the target skill's `SKILL.md` directly / sequential single-agent execution. The described behavior is what matters, not the exact tool name.

This skill owns everything from "tasks.md is ready" to "acceptance written": the 「执行方式」 selector, engine dispatch (including the task-swarm handoff), `implementation-log.md` appending, acceptance, and the distill prompt. It never generates requirements / design / tasks — earlier phases belong to the sibling `spec` / `intake` skills. Extracted from `../spec/SKILL.md` as a pure relocation: the semantics below are unchanged from the pre-6.3.0 inline pipeline.

## Entry contract (three callers, one behavior)

- **Pipeline entry**: the spec orchestration shell (`../spec/SKILL.md` Flow step 5) invokes this skill by name (`specode:execute`) via the `Skill` tool right after tasks.md is confirmed — slug and specsRoot are already in the conversation context; don't re-ask, but still run §Preflight to ground on on-disk state.
- **Manual entry**: the user types `/specode:execute <slug>` at any time (typically after a session break, or after `/specode:continue <slug>` reported an executing/complete phase). slug is **required** — missing → report an error and suggest `/specode:list`.
- **continue handoff**: when `/specode:continue <slug>` infers phase ∈ {executing, complete, legacy 5.x} and the user gives the go-ahead, the continue skill invokes this skill via the `Skill` tool instead of re-deriving execution rules from prose.

All three entries converge on the same flow: §Preflight → §执行方式 selector → §Execution dispatch → §Acceptance.

## Shared rules (inherited, cross-referenced — do not re-derive)

- **CLI resolver**: every specode CLI goes through the `run.sh` wrapper — relative to this skill that is `../../scripts/`; use this skill's base directory to make it absolute (no env-var resolution, no cache `find`, never bare `python3`):

  ```bash
  sh ../../scripts/run.sh ../../scripts/resolve_root.py <verb> <args...>
  ```

- **Core invariant (4 fixed docs)**: unchanged — see `../spec/SKILL.md` §Core invariant. This skill only appends to `implementation-log.md` and checks off `tasks.md` checkboxes; it never creates or renames artifacts.
- **Output language**: user-facing output (selector, progress, acceptance summary, errors) in **Chinese (中文)**; technical names / paths / code identifiers verbatim. **Document output brevity**: never reprint document bodies in chat (path + a few bullets only).

## Preflight (always run, all entries)

1. `resolve_root.py get-root` (**exit 3** → first-time setup; **exit 4** → specsRoot configured but **unreachable** — external drive not mounted / path gone → surface the cause and re-prompt the user for a path, do **not** treat it as "slug not found"; both per `../spec/SKILL.md` §specsRoot resolution) → on exit 0, locate `<specsRoot>/<slug>/`; directory missing → report an error and suggest `/specode:list`.
2. Read the fixed docs present and branch on plan state:

| On-disk state | Action |
|---|---|
| `tasks.md` has unchecked `- [ ]` | Normal path: §执行方式 selector → §Execution dispatch → §Acceptance. |
| no `tasks.md`, but `design.md` contains `## Task` + `- [ ]` | **Legacy 5.x spec**: treat `design.md` as the plan (pre-6.0.0 semantics) and proceed on the normal path. |
| no `tasks.md` (and not legacy) | Stop: report the spec hasn't reached the execution phase yet; suggest `/specode:continue <slug>` to finish requirements / design / tasks first. **Never generate tasks.md here.** |
| all `tasks.md` checkboxes checked | Skip selector + execution; go straight to §Acceptance (if `implementation-log.md` already carries an acceptance summary, report already complete instead). |

## 执行方式 selector (the single fixed per-spec selector)

Call `AskUserQuestion` to present **adaptive 4 options** — **show an option only if its engine is installed**. Pass the option label/description text below verbatim (they are user-facing selections and stay in Chinese):

1. **委托 task-swarm（多 agent 并发）** — requires task-swarm.
2. **superpowers subagent-driven（每 Task 派全新 subagent + 两阶段评审，推荐）** — requires superpowers.
3. **superpowers executing-plans（当前会话顺序批量 + checkpoint）** — requires superpowers.
4. **specode 自执行（顺序单 agent）** — native fallback, the only option when nothing is installed.

> Options 2/3 are both superpowers skills (built on the host CLI's built-in subagent capability), not specode built-in workflows; their ergonomics differ (the former: clean context + per-Task review; the latter: single-session continuous batch).

When presenting, pass question / header / options **verbatim** per the `references/selectors.md` example — do not invent and do not collapse into a shorter option set. There is no hard-check hook; "verbatim per the example" is enforced by this rule alone.

## Execution dispatch (branches by selector choice, all TDD)

- Delegate to task-swarm (installed) → see §task-swarm handoff below.
- superpowers subagent-driven (installed) → call `superpowers:subagent-driven-development`.
- superpowers executing-plans (installed) → call `superpowers:executing-plans`.
- specode self-execute (fallback) → the host agent runs TDD in `tasks.md` Task order (write failing test → run red → implement → run green), checking off each `- [ ]`.
- Append to `implementation-log.md` during execution.

**Availability check**: attempt to invoke the superpowers skill via the `Skill` tool first; if unavailable, take the native branch — same logic for task-swarm (`/task-swarm:swarm` invocation fails → fall back). Do not stall or tell the user to install something; pick up natively right away. Per-phase mapping details: `../spec/references/superpowers-wiring.md`.

## task-swarm handoff (zero hard dependency)

task-swarm is a **standalone plugin**; specode has **zero imports** of it and does not know its install path — all calls go through task-swarm's own `/task-swarm:swarm` skill (which self-locates its scripts via its own base directory). After the user picks "delegate":

1. Read this spec's `tasks.md` Task list + each Task's `**Files:**` + `(needs:)` → mechanically derive `<specsRoot>/<slug>/pipeline.yml` (merge Tasks into task groups by writes-conflict + needs topology / `@writes` files / `needs` topology).
2. **Show the yml summary to the user** (number of task groups / same-file conflicts / topology); init only after the user confirms.
3. Invoke task-swarm's own `/task-swarm:swarm` command to drive its plan → fork → advance → writeback → resolve orchestration until done.
4. Append to `implementation-log.md` throughout; run acceptance after done.

**task-swarm not installed** (`/task-swarm:swarm` unavailable) → fall back on the spot to "specode self-execute" or the superpowers execution path, so the user is never stuck. `pipeline.yml` is a transient artifact only — not one of the 4 fixed products.

## Acceptance (coding complete)

- superpowers installed → call `superpowers:verification-before-completion` (optionally also `superpowers:requesting-code-review`).
- not installed → **specode-native**: the host agent verifies item by item against the `AC-N` in `requirements.md` / `design.md`'s test strategy (测试策略) / all `tasks.md` checkboxes checked.
- Say "请验收" in prose and write an acceptance summary in `implementation-log.md`. **There is no formal acceptance-gate selector.**
- **distill is manual — leave a one-line reminder, do not prompt**: after acceptance is written, add a single passive line to the report, e.g.「如需把本次定位经验沉淀进项目 knowledge-base，可手动运行 `/specode:distill <slug>`」. Do **not** `AskUserQuestion` and do **not** auto-run distill — it stays a fully separate user-triggered command (`../distill/SKILL.md`). This keeps execute and distill decoupled (no gate, no config).

## References

- `references/selectors.md` — verbatim `AskUserQuestion` example for the 「执行方式」 selector (moved here from the spec skill in 6.3.0).
- `../spec/SKILL.md` — the pipeline that hands off to this skill (Core invariant, specsRoot resolution, Iron rules).
- `../spec/references/superpowers-wiring.md` — phase ↔ superpowers skill mapping and availability checks.
- `../spec/references/obsidian.md` — the full `resolve_root.py` verb table.
