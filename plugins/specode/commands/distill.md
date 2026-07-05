---
description: Manually distill a finished (or in-progress) spec into the project's `knowledge-base/` as atomic location knowledge points (cases/ + navigation/ + MEMORY.md). Optionally copy to an Obsidian vault. Manual trigger only — never auto-run.
---

`/specode:distill <slug>` — distill a single spec into **atomic location knowledge points**, landed in the spec's owning project `knowledge-base/`, optionally copied to an Obsidian vault.

Usage:

- `/specode:distill <slug>` — the slug must resolve to a directory under `<specsRoot>/`; `<slug>` is required.
- optional flag: `--target-dir <abs-path>` — specify the Obsidian copy directory directly (absolute path; written directly, no concatenation); if omitted, distill ends by asking via `AskUserQuestion` whether to copy and where.

Behavior: invoke the `distill` skill, which distills atomic knowledge points (two types: case / navigation) purely from the spec docs + current agent context → lands them in the project `knowledge-base/` → rebuilds the MEMORY.md index → optional Obsidian copy. The full flow is authoritative in `skills/distill/SKILL.md`.

> Recommended to run **after execution + acceptance are complete**: distilling "landed + verified" knowledge points has the highest value; distilling an unfinished spec risks pointers into unbuilt code (distill Step 1's completion check warns about this).

Red lines (v5.1+):

- **Primary write domain = `<project_root>/knowledge-base/`** (`cases/` + `navigation/` + `MEMORY.md`); Obsidian is an **optional copy**, not the default primary product.
- Spec dir **read-only**: never modify any file under `<specsRoot>/<slug>/`.
- **md-only**: produces only markdown, no yml, no silent injection.
- `--target-dir` / the user-entered path is **written directly, no concatenation**; under `/Volumes/`, verify the mount first.
- `knowledge-base/` is not committed to the repo (`ensure-gitignore` guarantees it on landing).
- `project_root` is read via `resolve_root.py read-project-root --spec ...`, **not re-derived from cwd**.
- **Manual trigger only** — the main specode flow never auto-invokes it; acceptance only offers the entry point.

> Need the v3 behavior (auto-trigger + writing yml to `.ai-memory/knowledge/`)? checkout `backup/specode-v3.4.0-task-swarm-v0.9.2`.
