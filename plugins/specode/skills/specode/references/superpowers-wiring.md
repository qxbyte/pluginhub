---
description: Use when specode needs to invoke a superpowers skill at a given phase, or determine whether to fall back to native — phase↔skill mapping, artifact placement double-check, and fallback matrix.
---

# superpowers orchestration mapping

| Phase | superpowers installed | Absent → specode-native |
|---|---|---|
| Clarification + requirements + design | superpowers:brainstorming (one call spans both phases, dual artifacts) | AskUserQuestion clarification + write per requirements template; author design.md per the design template (传统设计文档) |
| Executable plan (tasks) | superpowers:writing-plans → tasks.md | Self-decompose Tasks + TDD steps per the tasks template |
| Execution | task-swarm / superpowers:subagent-driven-development / superpowers:executing-plans | Sequential TDD following tasks.md Tasks |
| Acceptance | superpowers:verification-before-completion (+ requesting-code-review) | Verify each AC-N / design.md 测试策略 / tasks.md checkbox in order |

## Artifact placement (double-check, invariant enforcement)
1. Pre-call: when invoking a skill, explicitly pass the target absolute path(s) and fixed filename(s) — brainstorming → **both** `requirements.md` (澄清结论) and `design.md` (设计展示, per the design template sections); writing-plans → `tasks.md` (also instruct it to skip its own execution-handoff question — specode's 执行方式 selector supersedes it).
2. Post-call: after the skill returns, verify that every expected `<specsRoot>/<slug>/<fixed-name>` is in place (brainstorming: check **two** files); if not, move/rename the skill's actual output to that path.

## Availability check
Attempt to invoke superpowers via the Skill tool first; if unavailable or not installed, take the native branch. Same logic applies to task-swarm (if `/task-swarm:swarm` invocation fails, fall back to native).
