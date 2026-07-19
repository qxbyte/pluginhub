---
name: swarm
description: Use when driving the task-swarm multi-agent orchestrator standalone — read a requirement or design doc, generate a pipeline.yml, then run the fork → review → validate loop to finish a multi-task implementation. Trigger /task-swarm:swarm, or when specode delegates its execution phase here; input a requirements doc or a hand-written pipeline.yml.
---

# task-swarm — standalone multi-agent orchestration (`/task-swarm:swarm`)

> **Host-tool convention** 🔧: this skill orchestrates by dispatching subagents ("fork") and reading their completion status. Mechanism names — the `Task`/`Agent` tool (dispatch a subagent), the `Explore` agent (a read-only investigation subagent), the subagent run-status display ("teammates UI", the ✓/streaming/running indicators) — are written for Claude-family hosts (Claude Code / CodeBuddy), where naming them directly is the most reliable. On a host that lacks a given mechanism, use its nearest equivalent (a subagent-dispatch tool / a read-only subagent / whatever surfaces subagent completion); with no subagent capability at all, run the groups sequentially as a single agent. A subagent counts as done only when the host confirms its dispatched task returned successfully — never from the subagent's own verbal report. The described behavior matters, not the exact tool name.

## §0 Who you are

The lead agent = task-swarm's **orchestrator + planner**. task-swarm provides four things:
the pipeline.yml orchestration format, the state-machine CLI (`task_swarm.py`), the sub-agent role
definitions (coder/reviewer/validator), and report rendering.

The CLI **only guards 4 points of mechanical integrity**; all other orchestration judgment is yours, and the CLI does not constrain your thinking:
1. schema validation (pipeline.yml format is legal)
2. agent_key consistency (state machine and artifacts line up)
3. advance artifact completeness / format checks
4. atomic writes + blocking manual edits to controlled files

task-swarm **runs standalone and does not depend on specode**. If specode is also installed, the specode
side delegates into it — but that is still specode calling task-swarm's standalone interface, not reverse coupling.

### Delegated mode (when integrated by an upper-layer spec workflow)

When delegated by an upper-layer spec workflow, `init` additionally carries `--spec-id <id>` / `--spec-dir <dir>`,
two **optional traceback parameters**, used only to tag this run to its source requirement for report traceback;
task-swarm's own behavior, state persist location, and state machine are unchanged. After the run's `resolve`
finalizes, the calling lead agent (per its own workflow's rules) decides the next step — task-swarm neither
perceives nor drives the caller's subsequent phases.

## §1 Script invocation (relative path, superpowers-style)

All `task_swarm.py` calls go through the `run.sh` wrapper. The scripts live in the plugin's `scripts/` directory —
relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an
absolute one (do **not** resolve env vars, do **not** `find` the cache). Never call a bare `python3`. Shell state
does not persist between Bash calls, so every call is self-contained:

```sh
sh ../../scripts/run.sh ../../scripts/task_swarm.py <subcmd> <args...>
```

## §2 Entry routing

The first thing the user gives you decides the path:

- **A `pipeline.yml`** (or any .yml that passes schema validation) → the power-user hand-wrote the orchestration → skip the planner, go straight to §4 init.
- **A requirements doc** (design.md / requirements / superpowers plan / bare .md) → act as **lead-agent-doubling-as-planner** (§3): read the requirement → produce `pipeline.yml` (fork an `Explore` sub-agent when you need to inspect the codebase, then you synthesize) → persist to `<project-root>/.task-swarm/pipeline.yml` → then §4 init.
- **No arg / ambiguous** → ask the user in chat for a requirements doc or pipeline.yml path; do not invent one.

standalone: no session / lock concept, the user can trigger it directly. State persists under `<workdir>/.task-swarm/runs/`.

## §3 Lead agent as planner — generate a compliant pipeline.yml

- Read the requirement doc and understand what to build. When you need the codebase's current state, **fork an `Explore` sub-agent to investigate**, but **you** synthesize the findings into the yml — the planner role is yours, not the sub-agent's.
- Split into `task_group`s (semantic task groups); the task points within each group obey:
  - `@writes` (`writes:` in the yml) must not intersect across **concurrent-eligible groups**; conflicting files must be serialized, expressed via `needs` topology
  - granularity 30min–2h to complete; split anything too large; do not hard-bind dependencies when work can run concurrently
  - each task group is paired with a reviewer + validator
- **Write the format per `references/pipeline-yaml.md`, not from memory** (a restricted YAML subset; see that doc for pitfalls)
- After writing, run `init --pipeline` to trigger schema validation; on errors, fix the yml per the hints and retry (**self-fix loop**, until init succeeds)

## §4 init

```sh
sh ../../scripts/run.sh ../../scripts/task_swarm.py \
   init --pipeline "<absolute path to pipeline.yml>" --workdir "<project root>" \
   [--project-root "<code root>"] [--spec-id <id>] [--skip-validator] [--serial-validation]
```

- `--pipeline`: absolute path to pipeline.yml, the **only input** (semantic task groups + cross-group `needs` deps + per-group task `writes`).
- `--workdir`: state persist root (state root = `<workdir>/.task-swarm/runs/`). Defaults to cwd; in standalone mode use the project root.
- `--project-root` (optional): root of the code being changed (defaults to `--workdir`).
- `--skip-validator`: manual-acceptance mode — after review/p0-fix, skip validation/v-fix and writeback directly.
- `--serial-validation`: make the **validator globally serial** under cross-group concurrency (only one group's validation/v-fix runs at a time). Add this when tests share resources / clash on ports.
- init reports "no task groups resolved" → pipeline.yml format is wrong; fix per `references/pipeline-yaml.md` and retry.
- Once you get `{run_id, run_dir, groups, skip_validator}`, move to §5.

## §5 The 7-step loop (plan → fork → wait for all to complete → advance → writeback → resolve → report)

Every subcommand uses the §1 wrapper (`sh ../../scripts/run.sh ../../scripts/task_swarm.py <subcmd> ...`):

1. `init` (done in §4)
2. `plan --run <run_id>` returns the **multi-group concurrent schedule**: `{schedule:{done,running,runnable,blocked,failed}, actions:[...], serial_validation, max_parallel}`. `actions` lists the `fork` set for each runnable/advanceable group; `schedule.runnable` is the groups startable now, `blocked` gives the reason (`needs` unmet / `writes` conflicts with a running group).
3. `fork`: in a single message, fork the coders for **all runnable groups** in `actions` together (copy each `fork[].agent_key` **verbatim**, **never** invent `coder-fix-xxx`). Total concurrency is bounded by `max_parallel` — overflow groups carry to the next round.
4. **Wait for all in-flight Tasks to be ✓ completed before you advance** (hard constraint):
   - You must see every forked Task ✓ completed via the host's subagent run-status display (the teammates UI on Claude Code); any still-streaming / still-running subagent blocks advance.
   - **Do not** judge completion from verbal reports — only a subagent's own dispatch tool returning ✓ (the `Task` tool on Claude-family hosts) counts.
   - When unsure, call `plan --run <run_id>`; if it returns `coding-waiting`/`p0-fix-waiting`/`v-fix-waiting`, go back to waiting.
5. `advance --run <run_id> --group <gid> --phase <p>` (gid is a string like `g1`) advances **that group's** sub state machine.
6. `writeback --run <run_id> --group <gid>` (finalize this group, does not write tasks.md).
7. All groups done → `resolve --run <run_id>` to finalize → `report --run <run_id>` for the report.

> plan's `schedule` is the concurrency-driving core: the lead agent forks multiple groups from `runnable` in one message, `running` are the groups in flight, `blocked` (`needs` unmet / `writes` conflicts with a running group) enter runnable only on a later plan once unblocked.

Full spec in `references/task-swarm.md` (skim TOC + §3 state machine + §9 CLI quick reference before acting).

### heartbeat (optional for long runs)

The lead agent may call this every 5 minutes / after each subagent finishes to refresh `last_activity_at`:

```sh
sh ../../scripts/run.sh ../../scripts/task_swarm.py heartbeat --run <run_id>
```

## §6 Mechanical discipline (maps to the CLI's 4 guard points)

- **Before advance you must wait for all the group's forked Tasks ✓ completed**; no streaming/running Bash may `advance --group <gid>`. When unsure, call `plan --run <id>`; if it returns a `*-waiting` action, return to waiting.
- **Do not invent agent_key**: use the canonical names plan gives you (`coder-{gid}-s{n}-r1`, `reviewer-{gid}-r1`, `validator-{gid}-r1`, `coder-vfix-{gid}-r{R}-f{I}`, etc., gid = group id such as g1); do not make up `coder-fix-xxx`.
- **result.md missing STATUS** → re-fork the **same-named** agent (clear its outbox first: `rm -rf agents/<key>/outbox/*`); **never hand-patch STATUS** (a missing STATUS usually means the subagent exited early and code was not flushed to disk). If `status --run <id>` shows it still in_flight → wait; >10 min with no finalize → escalate to cancel + report to user.
- **Do not manually edit controlled files** (state.json / outbox artifacts) — the CLI will exit 2 to block it.

## §7 Terminology: reviewer severity vs validator fail (easily confused)

| Concept | Source | Triggers fix loop? |
|---|---|---|
| **P0 (with evidence tag)** | reviewer `review.md` `## P0`, must carry `[req:x.y]`/`[security]`/`[contract]` | ✓ p0-fix (one round only, no re-review, goes straight to validation) |
| **P0 (no evidence tag)** | reviewer `## P0` missing the tag | downgraded to advisory → ✗ not fixed |
| **P1 / P2** | reviewer `## P1`/`## P2` | ✗ advisory, not fixed |
| **validator fail** | validator `validation.md` `## 判定 = fail` | ✓ v-fix loops until pass; 3 consecutive rounds with the same fail signature → `failed-deadloop` |

The validator **does not emit P0/P1/P2 tags**; its fix_targets are all "task not finished", and a fail must be fixed.
If the user asks "can I skip it" → by design no; the only way is to abort the run + edit pipeline.yml to remove that task and re-init.

## §8 Exception exits

coder STATUS=failed/blocked, writeback out-of-bounds, `failed-deadloop` (3 consecutive rounds with the same fail signature)
→ **stop the loop, report to the user, wait for user intervention; do not auto-retry**. See `references/task-swarm.md` §3 / §8.

## §9 No-specode-dependency declaration

This SKILL does not reference any specode session script, selector, or acceptance stage. State persists to
`<workdir>/.task-swarm/runs/<run_id>/`. Standalone mode has no spec-lock concept and no session gate —
the user can trigger it directly with `/task-swarm:swarm <requirement doc>`.
