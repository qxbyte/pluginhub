---
name: list
description: Use when listing all specs under the specs root — the /specode:list entry that shows every spec slug with its inferred phase, for looking up slugs or an overview; it does not resume. Trigger /specode:list.
---

# /specode:list — list all specs

Lists every spec under `<specsRoot>` with each one's inferred phase (for looking up slugs / overview). **Does not resume.**

## Resolver

specode CLIs go through the `run.sh` wrapper in the plugin's `scripts/` directory — relative to this skill that is `../../scripts/`; use this skill's base directory to turn the relative path into an absolute one (do **not** resolve env vars, do **not** `find` the cache):

```bash
sh ../../scripts/run.sh ../../scripts/resolve_root.py list-specs
```

## Flow

1. `resolve_root.py get-root`: exit 3 (not configured) → first-time setup (see `../spec/SKILL.md` §specsRoot resolution), then continue; exit 0 → `<specsRoot>`.
2. `resolve_root.py list-specs` to list slugs; for each slug, read its spec directory documents and infer the current phase per the documents-as-state table in `../continue/SKILL.md`, then display slug + phase.
3. No specs found → prompt the user with `/specode:spec <request>`. **Do not resume.**

## Output Language

User-facing output must be in **Chinese (中文)**.
