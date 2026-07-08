---
description: One-page mental model of specode's experience/knowledge loop — who produces, who indexes, who reads, and when. Read this to understand how distill / knowledge-base / MEMORY / ragkit / intake-retrieval fit together.
---

# Knowledge-flow mental model (who produces · indexes · reads · when)

In one line: **the KB is "for locating, not for facts".** It only supplies pointers (file paths + call chains + navigation experience) to help you jump to real code faster; **real code is always the only source of truth**. Never advance a new requirement on KB content alone.

```
  produce (write)                   index                     consume (read)
  ─────────────────────────         ───────────────           ─────────────────────────────
  /specode:distill <slug>           MEMORY.md                 intake (requirements analysis)
   (manual; prompted at the         (small md index,          = primary retrieval node
    end of acceptance per            columns 标题/类型/         · Tier-1: read MEMORY, match page/field/domain
    auto_distill; never              描述/来源/路径/tags)       · hit → Tier-2: read ≤5 points → jump to real code
    auto-run)                            ▲                     · if ragkit present and chunks.json exists
        │                                │ memory-rebuild        → Tier-0 ragkit:query multi-recall
        ▼                                │ (rebuilt in full          │
  <project_root>/knowledge-base/     from each doc's               ▼
   ├── cases/<topic>.md    ────────► frontmatter,             design (conditional top-up)
   ├── navigation/<topic>.md         never hand-edited)       = inherits intake's pointers by default,
   └── MEMORY.md                     .ragkit/ (optional)        re-queries only for new territory
        │                            chunks.json + vectors          │
        │ (optional copy)            built by /ragkit:embed         ▼
        ▼                            (only when ragkit          ground design/requirements to real code
   Obsidian vault                     installed)               (tasks / execution / task-swarm = zero injection)
   (knowledge.py copy-to,
    human-readable mirror)
```

## Iron rules

- **Production is manual**: only `/specode:distill <slug>` writes the KB; the main flow never auto-sediments (acceptance only *offers* the entry point, gated by `auto_distill`).
- **Frontmatter is the single source of truth**: `MEMORY.md` is always rebuilt in full by `knowledge.py memory-rebuild` from each doc's frontmatter, **never hand-edited** (`memory-validate` checks for drift).
- **Consumption happens in only two places**: intake's project-analysis step (primary node) + design (conditional top-up). **tasks / execution / task-swarm inject nothing** — by then the file paths are already in design.md / tasks.md.
- **Injection is pointers, not facts**: pasted as a `参考定位（非事实来源）` section, used only for locating, never written as a factual conclusion in requirements.md.
- **Fully opt-in**: no `knowledge-base/MEMORY.md` → retrieval is silently skipped (default cost ≈ one small index read). No ragkit → Tier-0 is inert, falls through to Tier-1/2.
- **`knowledge-base/` is not committed**: a local-private location asset (`ensure-gitignore` guarantees it); the Obsidian copy is an optional human-readable mirror.

## Contract lockstep 🔒

The MEMORY columns + frontmatter keys must agree across three sites: `skills/distill/references/doc-template.md` (writes), `scripts/knowledge.py` `_COLS` (indexes), `skills/spec/references/retrieval.md` (reads). Change one → change all three. `tests/test_contract_lockstep.py` is the CI gate for this discipline.

## Authoritative doc for each part

- Produce: `skills/distill/SKILL.md` + `skills/distill/references/doc-template.md`
- Index CLI: `scripts/knowledge.py` (`memory-rebuild` / `memory-validate` / `copy-to` / `ensure-gitignore`)
- Consume: `skills/spec/references/retrieval.md` (Tier-0 gate + two-tier gated)
- Primary consumer: `skills/intake/SKILL.md` §Step 2b
