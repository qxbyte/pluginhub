# specode experience-retrieval injection (Tier-0 gate + two-tier gated, model-driven prose)

> This file is the retrieval spec. **Primary caller = the project-analysis step (§Step 2b) of the `specode:intake` skill — the primary retrieval node**; the design phase does only a **conditional top-up** (inherits intake's located pointers by default, re-queries only when it opens new territory). All retrieval intelligence is prose here;
> **no extra script at runtime**: read `MEMORY.md` with the `Read` tool (it's a local file under `<project_root>/knowledge-base/`).

## Top-level invariant 🔒 (the reason this capability exists)

The KB is **for locating, not for facts**:
- For a new requirement, the model's implementation logic does **not** depend on the KB; the KB only supplies **pointers** (file paths + call chains + navigation experience).
- Once you have a pointer, **real code remains the only source of truth** — read, analyze, and change against it.
- The entire value of retrieval injection = **shortening the latency of locating the code to analyze**, not adding a source of truth.
- Forbidden: advancing a new requirement on KB content alone / treating a historical conclusion as the truth about current code.

## Trigger surface

- **Primary node = intake (the project-analysis step of the requirements phase)**: called by `specode:intake` §Step 2b, producing `参考定位（非事实来源）` pointers.
- **Design phase = conditional top-up**: **inherit intake's pointers by default, do not re-run a full retrieval**; re-query per this spec only when design opens territory intake didn't cover.
- **Tasks phase: no retrieval** — inherit the file paths already located in design.md.
- **Execution / task-swarm: zero injection** — pass no KB / retrieval artifact to task-swarm; it stays a pure executor of any spec.

## Precondition (whether to retrieve at all)

1. Get `project_root` via `resolve_root.py read-project-root --spec <specsRoot>/<slug>`.
2. Check whether `<project_root>/knowledge-base/MEMORY.md` exists.
   - **Absent** (fresh project / never distilled) → **silently skip the whole retrieval**; no error, no empty section, proceed normally into requirements/design.
   - Present → enter the retrieval flow below (try the Tier-0 gate first, fall through to two-tier gated).

## Tier-0 gate: RagKit (optional fast path, ahead of Tier-1)

This section is evaluated only after the precondition passes (MEMORY.md exists), and under the same trigger-surface constraint: **only intake (requirements project-analysis, primary) and design (conditional top-up); not triggered in execution / task-swarm**. Take this section only when **all** of the following hold; if any fails → skip it and run the two-tier gated flow below, and **do not read any RagKit doc/skill** (zero extra tokens):

1. `ragkit:query` is present in the session's available-skills list;
2. `test -f <project_root>/knowledge-base/.ragkit/chunks.json` holds (the index is built).

How to run it:
- The model **derives the query terms itself** from the current need (page name / field / functional domain / call chain, etc.) and calls the `ragkit:query` skill; **multiple rounds and multiple angles are allowed** until location is sufficient or you confirm there's nothing relevant.
- It returns location cards (pointers). Judge each semantically — a tags/lexical match ≠ relevance (same discipline as Tier-1); for adopted entries `Read` the source and jump to real code as in Tier-2; cap adopted entries under the same Tier-2 discipline (default ≤5 per phase, may exceed with a stated reason for complex needs).
- Injection still uses the `参考定位（非事实来源）` section from the "Injection format" below; once you hit and inject, **skip Tier-1/2**.
- Relay RagKit's degradation/hint output (the ╭─ RagKit ─╮ block) to the user verbatim.
- If multiple rounds confirm nothing relevant → exit this section and continue with the Tier-1/2 flow below.

This gate is **zero-dependency** on RagKit: specode does not read its internals; when RagKit is absent this section is simply inert (isomorphic to task-swarm's zero-import model).

## Two-tier gated retrieval

### Tier-1 (cheap by default)
1. `Read` `<project_root>/knowledge-base/MEMORY.md` (tiny cost). One knowledge point per row, columns:
   `| 标题 | 类型 | 描述 | 来源 | 路径 | tags |`.
2. Take the current need's **page name / field name / functional domain** keywords and compare against each row's `tags` + `描述`. **A `tags`/`描述` match is only a *candidate*, not relevance** — you must further judge whether the point's **change type / semantics** truly applies to the current need, and drop it if not. Example: the current need is "add a column to a list", and a "list field *masking*" case matched on its `列表页` tag, but masking is a different change type than adding a column → take only its "location-type" point (e.g. the list-page location routine), and **do not inject** the masking case. Blindly "inject on tag match" degrades into v3's noise injection and pollutes the context.
3. If nothing is (semantically) relevant → end retrieval; default cost is a single small index read.

### Tier-2 (expensive only on a hit)
4. `Read` the full text of matched points, **capped at ≤5 per phase**; read fewer when appropriate. **Soft cap**: for a complex need matching more points, you may **exceed 5 with a stated reason** in the `参考定位` section (N is a prose soft constraint anyway).
5. Use the doc's `前端文件 / 后端文件 / 调用链` fields to **jump to real code**, and analyze against the real code (real code is the only truth).
6. **Cross-requirement composition**: when several points hit, trace each one's `来源` back to its own change/location path and compose the references (e.g. new requirement 3 may hit both "requirement 1's masking case" + "requirement 2's list-location navigation", used together).

## Injection format

Paste the results as a conspicuous standalone section so downstream never mistakes it for fact:

```markdown
## 参考定位（非事实来源，仅用于快速定位真实代码）
- [来自 需求1-脱敏 / case] A页面脱敏：前端 src/pages/A/columns.tsx，后端 AccountDTO.java，链路 …
- [来自 需求2-列表列 / navigation] 列表页定位套路：…
> 以上仅为定位指针，**可能指向计划中 / 已重构 / 已移动的代码**。实际改动以当前真实代码为准，需逐一打开核对。
```

- In **intake (requirements project-analysis)**: this section helps analyze "which real code this requirement touches", as input for clarification / scoping; **not written as a factual conclusion in `requirements.md`** (handed to design as ephemeral context).
- In **design (conditional top-up)**: by default use intake's handed pointers to ground module boundaries / interface design to real code; re-query only when opening new territory. Design's judgment is still based on real code (the tasks phase no longer retrieves — it inherits the file paths already located in design.md).

## Schema ↔ reasoning table (change discipline 🔒)

> The KB schema and this retrieval prose are two faces of one contract and **evolve in lockstep**: change a MEMORY/frontmatter field → change this table and the matching steps together; no independent drift. The three sites (the frontmatter distill writes, `knowledge.py`'s MEMORY columns, this retrieval prose) must agree. The `tests/test_contract_lockstep.py` gate enforces this.

| MEMORY / KB field | how retrieval uses it |
|---|---|
| `tags` / keywords | **Tier-1 primary match key**: compare the current need's page/field/domain against it |
| `描述` | Tier-1 secondary relevance signal |
| `类型` (case/navigation) | decides read intent: case → borrow a same-type requirement's change; navigation → locate files/entry points |
| `来源` (slug) | **cross-requirement composition**: on multiple hits, trace each `来源` to compose its change/path |
| `路径` | the `Read` target after a Tier-2 hit (relative to `knowledge-base/`) |
| the doc's `前后端文件 + 调用链` | the springboard to real code (after reading, go read the real code) |

## Why this doesn't repeat v3

v3's deterministic Python recall auto-injected historical **content** and didn't save tokens; it was removed in 4.0.0. This route: (1) the engine is model judgment, not a script score; (2) reads only the small index by default; (3) injects pointers not facts, small and labeled `非事实来源`; (4) reads only on a hit, capped at N=5. Success criterion = **faster/more accurate location** (token-neutral is acceptable).
