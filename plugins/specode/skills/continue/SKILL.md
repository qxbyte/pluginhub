---
name: continue
description: Use when resuming an existing spec by slug — the /specode:continue entry that reads the fixed docs, reports a progress brief (inferred phase + checkbox progress), then stops and waits for the user; it never auto-resumes. Trigger /specode:continue <slug>.
---

# /specode:continue — resume an existing spec

> **Host-tool convention** 🔧: tool names in this skill — the `Skill` tool (invoke another skill by name), `AskUserQuestion` (structured multiple-choice question) — are written for Claude-family hosts (Claude Code / CodeBuddy), where naming them directly is the most reliable. On a host that lacks one, use its nearest equivalent (a skill-invocation mechanism / a structured-question tool); with no equivalent, fall back to reading the target skill's `SKILL.md` directly / plain-text prose. The described behavior is what matters, not the exact tool name.

`/specode:continue <slug>` loads an existing spec's context and reports where it stands, then **stops**. It never auto-resumes. This skill owns only the load-and-stop entry + phase inference; the actual pipeline lives in the sibling `../spec/SKILL.md`.

## Resolver

specode CLIs go through the `run.sh` wrapper in the plugin's `scripts/` directory — relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an absolute one (do **not** resolve env vars, do **not** `find` the cache):

```bash
sh ../../scripts/run.sh ../../scripts/resolve_root.py get-root
```

## Flow

1. slug is **required**; if missing → report an error and suggest `/specode:list` to find slugs.
2. `resolve_root.py get-root` (**exit 3** not configured → first-time setup; **exit 4** configured but **unreachable** — external drive not mounted / path gone → surface the cause and re-prompt for a path rather than reporting "slug not found"; both per `../spec/SKILL.md` §specsRoot resolution) → on exit 0, locate `<specsRoot>/<slug>/`; directory not found → report an error and suggest `/specode:list`.
3. Read every fixed doc present, infer the phase per the table below, then **report a progress brief and stop — do not auto-resume**.

**Load-and-stop 🔒**: `/specode:continue <slug>` never auto-resumes. It does exactly three things: (1) locate `<specsRoot>/<slug>/` and read every fixed doc present; (2) report a **progress brief** — slug, inferred phase, per-doc existence, tasks.md checkbox progress (x/N; legacy specs: design.md checkboxes), and what the next action *would* be; (3) **stop and wait for the user's instruction**. Only when the user says 继续 (or equivalent) does execution resume from the inferred phase; if the user instead supplies requirement changes, digest them into the affected docs first, then ask whether to resume. The "Resume action" column below describes what happens *after* the user gives the go-ahead — it is not automatic behavior.

| Directory state | Inferred phase | Resume action (after user go-ahead) |
|---|---|---|
| no `requirements.md` | intake | invoke the `specode:intake` skill via the `Skill` tool (project analysis + clarification + writes `requirements.md` with the frontmatter contract) |
| has `requirements.md`, no `design.md` | design | run design (brainstorming design-only / native authoring) |
| has `design.md`, no `tasks.md`, and `design.md` contains `## Task` + `- [ ]` | **legacy spec (5.x)** | invoke the `specode:execute` skill via the `Skill` tool (it detects the legacy design.md-as-plan itself) |
| has `design.md` (new-style, prose), no `tasks.md` | tasks | run tasks breakdown (writing-plans / native per tasks template) |
| `tasks.md` with unchecked `- [ ]` | executing | invoke the `specode:execute` skill via the `Skill` tool (it re-presents the 执行方式 selector / resumes the chosen engine) |
| all `tasks.md` checkboxes checked | complete | invoke the `specode:execute` skill via the `Skill` tool (it skips straight to acceptance) / report already complete |

## Resuming (only after the user gives the go-ahead)

When the user says 继续, resume from the inferred phase — **always by loading that phase's own instructions into context**, never by a bare prose cross-reference. A prose "see `../spec/SKILL.md`" does **not** load the file; a `Skill`-tool invocation or an explicit `Read` does. (This is the exact failure mode that motivated 6.3.0: the old continue said "resume per SKILL.md" but that SKILL was never loaded, so the 执行方式 selector couldn't be reconstructed.)

- Phase = **intake** → **invoke the `specode:intake` skill via the `Skill` tool** (it owns the whole requirements phase: project analysis + clarification + writing `requirements.md` with the frontmatter contract). Do **not** fall back to brainstorming — 6.x requirements always go through intake.
- Phase ∈ {**design, tasks**} → **`Read` `../spec/SKILL.md` first** to load the pipeline into context, then follow its §Flow (design = step 3, tasks = step 4), §superpowers orchestration + relocation, and §Iron rules. (design uses `superpowers:brainstorming` design-only or native; tasks uses `superpowers:writing-plans` or native — invoke those via the `Skill` tool where installed.)
- Phase ∈ {**executing, complete, legacy 5.x**} → **invoke the `specode:execute` skill via the `Skill` tool**. Never re-derive the 执行方式 selector or the engine dispatch from prose — that content lives only in `skills/execute/SKILL.md` and is loaded into context by invoking it.

The 4-doc fixed-artifact invariant and the `<specsRoot>/<slug>/` location are identical everywhere.

## Output Language

User-facing output (progress brief, questions, confirmations, errors) must be in **Chinese (中文)**.
