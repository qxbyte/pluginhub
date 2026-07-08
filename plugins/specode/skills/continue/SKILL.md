---
name: continue
description: Use when resuming an existing spec by slug — the /specode:continue entry that reads the fixed docs, reports a progress brief (inferred phase + checkbox progress), then stops and waits for the user; it never auto-resumes. Trigger /specode:continue <slug>.
---

# /specode:continue — resume an existing spec

`/specode:continue <slug>` loads an existing spec's context and reports where it stands, then **stops**. It never auto-resumes. This skill owns only the load-and-stop entry + phase inference; the actual pipeline lives in the sibling `../spec/SKILL.md`.

## Resolver

specode CLIs go through the `run.sh` wrapper in the plugin's `scripts/` directory — relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an absolute one (do **not** resolve env vars, do **not** `find` the cache):

```bash
sh ../../scripts/run.sh ../../scripts/resolve_root.py get-root
```

## Flow

1. slug is **required**; if missing → report an error and suggest `/specode:list` to find slugs.
2. `resolve_root.py get-root` (not configured → first-time setup: see `../spec/SKILL.md` §specsRoot resolution) → locate `<specsRoot>/<slug>/`; directory not found → report an error and suggest `/specode:list`.
3. Read every fixed doc present, infer the phase per the table below, then **report a progress brief and stop — do not auto-resume**.

**Load-and-stop 🔒**: `/specode:continue <slug>` never auto-resumes. It does exactly three things: (1) locate `<specsRoot>/<slug>/` and read every fixed doc present; (2) report a **progress brief** — slug, inferred phase, per-doc existence, tasks.md checkbox progress (x/N; legacy specs: design.md checkboxes), and what the next action *would* be; (3) **stop and wait for the user's instruction**. Only when the user says 继续 (or equivalent) does execution resume from the inferred phase; if the user instead supplies requirement changes, digest them into the affected docs first, then ask whether to resume. The "Resume action" column below describes what happens *after* the user gives the go-ahead — it is not automatic behavior.

| Directory state | Inferred phase | Resume action (after user go-ahead) |
|---|---|---|
| no `requirements.md` | intake | rerun requirements (brainstorming / native clarification) |
| has `requirements.md`, no `design.md` | design | run design (brainstorming design-only / native authoring) |
| has `design.md`, no `tasks.md`, and `design.md` contains `## Task` + `- [ ]` | **legacy spec (5.x)** | treat `design.md` as the plan per pre-6.0.0 semantics — resume execution / acceptance directly |
| has `design.md` (new-style, prose), no `tasks.md` | tasks | run tasks breakdown (writing-plans / native per tasks template) |
| `tasks.md` with unchecked `- [ ]` | executing | resume execution (task-swarm checks run state / superpowers resumes executing-plans / native resumes sequentially) |
| all `tasks.md` checkboxes checked | complete | run acceptance / report already complete |

## Resuming (only after the user gives the go-ahead)

When the user says 继续, resume from the inferred phase by following the pipeline in **`../spec/SKILL.md`** — its §Flow (design → tasks → 执行方式 selector → execution → acceptance), §执行方式 selector, §superpowers orchestration + relocation, §task-swarm handoff, and §Iron rules all apply unchanged. The 4-doc fixed-artifact invariant and the `<specsRoot>/<slug>/` location are identical. Read `../spec/SKILL.md` for the phase details.

## Output Language

User-facing output (progress brief, questions, confirmations, errors) must be in **Chinese (中文)**.
