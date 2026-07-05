---
description: Use when specode needs to invoke a superpowers skill at a given phase, or determine whether to fall back to native — phase↔skill mapping, artifact placement double-check, and fallback matrix.
---

# superpowers orchestration mapping

| Phase | producer | Absent → specode-native |
|---|---|---|
| Clarification + requirements | **`specode:intake`** (specode's own standalone skill — always; **not** superpowers) | intake is native to specode; there is no superpowers path here to fall back from. It always runs project analysis + clarification + writes `requirements.md` with the frontmatter contract. |
| Design (传统设计文档) | superpowers:brainstorming (**design only**, single artifact → design.md) | Author design.md per the design template |
| Executable plan (tasks) | superpowers:writing-plans → tasks.md | Self-decompose Tasks + TDD steps per the tasks template |
| Execution | task-swarm / superpowers:subagent-driven-development / superpowers:executing-plans | Sequential TDD following tasks.md Tasks |
| Acceptance | superpowers:verification-before-completion (+ requesting-code-review) | Verify each AC-N / design.md 测试策略 / tasks.md checkbox in order |

## Artifact placement (double-check, invariant enforcement)
`requirements.md` is written directly by `specode:intake` at the fixed path — **no relocation needed**. Only design/tasks are delegated to superpowers and need the belt-and-suspenders check:

1. Pre-call: when invoking a skill, explicitly pass the target absolute path + fixed filename — brainstorming → `design.md` (design only; requirements are already settled in `requirements.md`, tell brainstorming to read it as input and go straight to design); writing-plans → `tasks.md`.
2. **writing-plans' execution-handoff question**: writing-plans ends by asking "Subagent-Driven vs Inline Execution". It has no flag to disable this. **Ignore that question — do not act on it**; specode's 执行方式 selector supersedes it. (This is "digest", not "suppress" — you cannot actually stop it from asking.)
3. **brainstorming's terminal handoff**: brainstorming is hardcoded to end by invoking writing-plans. That happens to match specode's design → tasks order, so let it flow naturally into the tasks phase — just make sure design.md landed first.
4. Post-call: after the skill returns, verify the expected `<specsRoot>/<slug>/<fixed-name>` is in place (brainstorming → design.md; writing-plans → tasks.md); if not, move/rename the skill's actual output there.

## Availability check
Requirements always uses `specode:intake` (invoke it via the Skill tool). For design / tasks / execution / acceptance, attempt to invoke the superpowers skill via the Skill tool first; if unavailable or not installed, take the native branch. Same logic applies to task-swarm (if `/task-swarm:swarm` invocation fails, fall back to native).
