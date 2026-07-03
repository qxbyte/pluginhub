---
description: Load an existing spec's context by slug — reads the fixed docs, reports a progress brief (inferred phase + checkbox progress), then stops and waits for the user's instruction; never auto-resumes.
argument-hint: "<slug>"
---

# /specode:continue — resume a spec

`$ARGUMENTS` is the spec slug (required). Resolve the plugin root + run.sh as in `/specode:spec` (env var → cache-glob fallback):
```bash
R="${CLAUDE_PLUGIN_ROOT:-$CODEBUDDY_PLUGIN_ROOT}"; [ -f "$R/scripts/run.sh" ] || R="$(find "$HOME/.claude/plugins/cache" "$HOME/.codebuddy/plugins/cache" -path '*/specode/*/scripts/run.sh' 2>/dev/null | sort -V | tail -1)"; R="${R%/scripts/run.sh}"
sh "$R/scripts/run.sh" "$R/scripts/resolve_root.py" get-root
```

1. slug is required; if missing → report error and suggest `/specode:list` to find slugs.
2. `resolve_root.py get-root` (not configured → first-time setup per SKILL.md §specsRoot) → locate `<specsRoot>/<slug>/`; directory not found → report error and suggest `/specode:list`.
3. Read the spec directory documents, infer the phase per SKILL.md "documents as state" rule, then **report a progress brief and stop — do not auto-resume**:
   - Brief contents: slug, inferred phase, which fixed docs exist (`requirements.md` / `design.md` / `tasks.md` / `implementation-log.md`), tasks.md checkbox progress (x/N; legacy 5.x specs: design.md checkboxes), and what the next action would be.
   - Wait for the user's next instruction. "继续" (or equivalent) → resume from the inferred phase per SKILL.md §Continuation. Requirement changes/additions → digest them into the affected docs first, then ask whether to resume.
