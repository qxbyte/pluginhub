---
description: Use when resolving the spec document root directory, performing first-time directory setup, or listing specs with `/specode:list` — specsRoot three-tier resolution and directory conventions.
---

# specsRoot resolution and directory conventions

## Root source: single storage, single access point

specsRoot (the user's document management directory) is **stored in exactly one place**: the `specsRoot` key in `~/.config/specode/config.json`. Every script and command that needs this directory fetches it via `resolve_root.py get-root` — that is the **only access point**; nothing else should read the config directly.

`get-root` resolution order:
1. `--root` flag / env `SPECODE_ROOT` (temporary override for power users; not persisted)
2. `specsRoot` in `~/.config/specode/config.json` (**normal source**, used in every session)
3. Not found (no config) → **script cannot resolve = model cannot resolve** → model calls `AskUserQuestion` to ask the user for their document management directory (absolute path) → `resolve_root.py set-root --root <abs>` **writes it directly to the config file above** → all subsequent sessions read from config and will not ask again.

CLI via run.sh: `resolve_root.py get-root` / `set-root --root P` / `list-specs` (for the question example, see `selectors.md` §First-time directory setup).

## verbs (`resolve_root.py`, all via run.sh + absolute plugin-root)

| verb | Purpose | exit |
|---|---|---|
| `get-root [--root P]` | Resolve specsRoot (`--root` > env `SPECODE_ROOT` > config.specsRoot) | 0 ok / 3 unconfigured |
| `set-root --root <abs>` | Absolute path, persisted to `~/.config/specode/config.json.specsRoot` | 0 / 1 path not absolute |
| `list-specs [--root P]` | List spec slugs under root: subdirs with any fixed doc (`requirements.md` / `design.md` / `tasks.md` / `implementation-log.md`) **plus empty subdirs (intake)**; hidden dirs excluded | 0 / 3 unconfigured |
| `resolve-project-root [--cwd P]` | Compute the project_root default (`git rev-parse --show-toplevel` of cwd, else cwd) for the user to confirm | 0 |
| `write-project-root --spec <dir\|file> --root <abs>` | **Single writer** of project_root → spec's requirements.md frontmatter (validates absolute / dir exists / `/Volumes` mounted) | 0 / 1 invalid |
| `read-project-root --spec <dir\|file>` | **Single reader** of project_root from requirements.md frontmatter — all downstream skills use this | 0 / 3 missing field / 4 invalid value |
| `plan-unchecked --spec <dir\|file>` (alias `design-unchecked`) | Count unchecked `- [ ]` in the plan (tasks.md; 5.x legacy: design.md) | 0 all-checked / 2 has-unchecked (prints N) / 3 no-plan |
| `read-defaults [--key K] [--json]` | Read autonomous-mode defaults (env > `~/.config/specode/defaults.json` > schema). Single key → plain value; `--json` / no `--key` → `{value, source}` JSON | 0 / 1 unknown key |
| `write-default --key K --value V` | Persist a defaults key. 5 valid keys: `interactive` / `project_root_default` / `execution_mode_default` / `auto_distill` / `specs_root_default`; type + execution_mode whitelist validated | 0 / 1 invalid |
| `reset-default --key K \| --all` | Remove one key or `--all` wipe | 0 / 1 invalid |

Autonomous-mode behavior (when to skip each `AskUserQuestion`) is specified in `references/autonomous-mode.md`.

## Directory conventions
- The directory the user provides is used **verbatim** as the specs root; specode appends no internal sub-structure (the user may supply a fully qualified path such as `.../spec-in/<os>-<user>/specs`).
- Each spec = `<specsRoot>/<slug>/`, containing the fixed files `requirements.md` / `design.md` / `tasks.md` / `implementation-log.md`.
- `pipeline.yml` is generated only when delegating to task-swarm; it is not a fixed artifact.
- project_root = the project a spec targets. It is the **single join key** between a spec and its project, stored in **exactly one place** — the spec's `requirements.md` YAML frontmatter — and accessed only through `resolve_root.py {resolve,write,read}-project-root`. Default is `git rev-parse --show-toplevel` of cwd (fallback cwd), **confirmed once via `AskUserQuestion`**, then persisted to frontmatter by `write-project-root`. Later phases/skills (task-swarm; distill for relative-path resolution) read it via `read-project-root` — never re-derive from cwd/workdir, never guess.

## Documents as state (phase inference)
| Directory state | Phase |
|---|---|
| No requirements.md | intake |
| requirements.md present, no design.md | design |
| design.md present (contains `## Task` + `- [ ]`), no tasks.md | legacy 5.x spec — design.md is the plan; executing/complete by its checkboxes |
| design.md present (new-style prose), no tasks.md | tasks |
| tasks.md present, unchecked `- [ ]` remain | executing |
| All tasks.md checkboxes checked | complete |

(The full continuation table, including load-and-stop semantics, lives in SKILL.md §Continuation.)
