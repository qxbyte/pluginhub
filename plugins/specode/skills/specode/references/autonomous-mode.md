---
description: Use at every AskUserQuestion gate in the specode flow to decide whether to skip the prompt and use a persisted default (autonomous / CI mode) — the interactive master switch, the 5 defaults keys, and the skip decision.
---

# Autonomous-mode defaults (v3.4.0 / v0.9 M1/M9)

specode's user gates (`AskUserQuestion`) block in autonomous / CI runs where no human is present. This reference specifies how each gate decides to **skip the prompt and use a persisted default** instead.

## The rule 🔒

At **every** `AskUserQuestion` call site, first read the relevant default + its source via `resolve_root.py read-defaults --key <relevant> --json`. When `interactive == false` **and** that key's `source ∈ {env, file}` (i.e. the effective value is not the schema default), **skip the prompt and use the default** — this is the autonomous / CI path. When `interactive == true` (schema default), all gates behave exactly as before — **default behavior is unchanged**.

## Gate → key → env var mapping

| SKILL gate | defaults key | env var |
|---|---|---|
| First-time specsRoot setup | `specs_root_default` | `SPECODE_SPECS_ROOT_DEFAULT` |
| project_root confirmation (intake Step 1) | `project_root_default` | `SPECODE_PROJECT_ROOT` |
| 执行方式 selector (after tasks) | `execution_mode_default` | `SPECODE_EXECUTION_MODE` (values: `ask` / `task-swarm` / `superpowers-subagent` / `superpowers-executing` / `specode-self`) |
| distill prompt (acceptance end) | `auto_distill` | `SPECODE_AUTO_DISTILL` |
| Master switch | `interactive` | `SPECODE_INTERACTIVE` |

## Decision (pseudo-code, applies at each call site)

```bash
# 1) Read both keys via resolve_root.py (through run.sh + absolute root)
INTERACTIVE=$(... read-defaults --key interactive --json | jq -r '.value')
DEFAULT_INFO=$(... read-defaults --key <relevant-key> --json)
DEFAULT_VALUE=$(echo "$DEFAULT_INFO" | jq -r '.value')
DEFAULT_SOURCE=$(echo "$DEFAULT_INFO" | jq -r '.source')

# 2) Skip AskUserQuestion if non-interactive + has an effective (non-schema) default
if [ "$INTERACTIVE" = "false" ] && [ "$DEFAULT_SOURCE" != "default" ] && [ -n "$DEFAULT_VALUE" ]; then
  use "$DEFAULT_VALUE"   # silent path — autonomous / CI
else
  ask via AskUserQuestion  # original interactive path
fi
```
