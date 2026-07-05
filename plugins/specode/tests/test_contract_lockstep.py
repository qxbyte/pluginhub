"""Contract-lockstep tests — turn the "变更纪律" prose into a CI gate.

The MEMORY/frontmatter contract is documented in three places that CLAUDE.md
requires to stay byte-identical:
  1. scripts/knowledge.py — `_COLS` (what memory-rebuild actually emits)
  2. skills/specode/references/retrieval.md — the columns the retrieval reader expects
  3. skills/distill/references/doc-template.md — the columns/frontmatter distill writes

These tests read knowledge.py's ACTUAL emitted header (behavioral, not source
introspection) and compare it against the columns documented in the two .md
files, plus assert the doc-template frontmatter keys match what knowledge.py
reads. Reorder / add / drop a column in any one site → a test fails.
"""
from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_MD = PLUGIN_ROOT / "skills" / "specode" / "references" / "retrieval.md"
DOC_TEMPLATE_MD = PLUGIN_ROOT / "skills" / "distill" / "references" / "doc-template.md"

EXPECTED_COLS = ["标题", "类型", "描述", "来源", "路径", "tags"]
# frontmatter keys distill writes / knowledge.py reads (路径 is derived from the
# file path, not a frontmatter key, so it is NOT in this set)
EXPECTED_FM_KEYS = {"标题", "类型", "描述", "来源", "tags"}


def _write_doc(kb: Path, rel: str, *, 标题, 类型, 来源="", tags=None, 描述=""):
    p = kb / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    taglist = "[" + ", ".join(tags or []) + "]"
    fm = (
        "---\n"
        f"标题: {标题}\n"
        f"类型: {类型}\n"
        f"来源: {来源}\n"
        f"tags: {taglist}\n"
        f"描述: {描述}\n"
        "---\n\n# body\n"
    )
    p.write_text(fm, encoding="utf-8")


def _extract_memory_cols(text: str):
    """Return the MEMORY column header as a list of cells, found generically
    (order-preserving) so a reorder in any source is detectable. Matches the
    first pipe-run (no backtick/newline inside) that contains both 标题 and
    tags — works for a clean markdown table (knowledge.py output) and for an
    inline-code row inside prose (the two .md files)."""
    for m in re.finditer(r"\|(?:[^\n`|]*\|)+", text):
        cells = [c.strip() for c in m.group(0).strip().strip("|").split("|")]
        cells = [c for c in cells if c]
        if "标题" in cells and "tags" in cells:
            return cells
    return None


def _first_frontmatter_keys(text: str):
    """Keys of the first `--- ... ---` block (may sit inside a code fence)."""
    keys = []
    in_fm = False
    for line in text.splitlines():
        s = line.strip()
        if s == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm and ":" in s:
            keys.append(s.split(":", 1)[0].strip())
    return keys


def test_knowledge_emits_expected_columns(run_script, tmp_path: Path):
    """knowledge.py's actual MEMORY header == the canonical contract."""
    kb = tmp_path / "knowledge-base"
    _write_doc(kb, "cases/x.md", 标题="T", 类型="case", 来源="s", tags=["a"], 描述="d")
    res = run_script("knowledge.py", "memory-rebuild", "--kb", str(kb))
    assert res.returncode == 0, res.stderr
    emitted = _extract_memory_cols((kb / "MEMORY.md").read_text(encoding="utf-8"))
    assert emitted == EXPECTED_COLS, f"knowledge.py emits {emitted}"


def test_retrieval_md_columns_match_knowledge(run_script, tmp_path: Path):
    """The columns documented in retrieval.md == what knowledge.py emits."""
    kb = tmp_path / "knowledge-base"
    _write_doc(kb, "cases/x.md", 标题="T", 类型="case", 来源="s", tags=["a"], 描述="d")
    run_script("knowledge.py", "memory-rebuild", "--kb", str(kb))
    emitted = _extract_memory_cols((kb / "MEMORY.md").read_text(encoding="utf-8"))
    documented = _extract_memory_cols(RETRIEVAL_MD.read_text(encoding="utf-8"))
    assert documented is not None, "retrieval.md has no MEMORY column row"
    assert documented == emitted, (
        f"retrieval.md columns {documented} != knowledge.py {emitted} — "
        f"the 3-site contract drifted (变更纪律)"
    )


def test_doc_template_columns_match_knowledge(run_script, tmp_path: Path):
    """The columns documented in distill's doc-template == what knowledge.py emits."""
    kb = tmp_path / "knowledge-base"
    _write_doc(kb, "cases/x.md", 标题="T", 类型="case", 来源="s", tags=["a"], 描述="d")
    run_script("knowledge.py", "memory-rebuild", "--kb", str(kb))
    emitted = _extract_memory_cols((kb / "MEMORY.md").read_text(encoding="utf-8"))
    documented = _extract_memory_cols(DOC_TEMPLATE_MD.read_text(encoding="utf-8"))
    assert documented is not None, "doc-template.md has no MEMORY column row"
    assert documented == emitted, (
        f"doc-template.md columns {documented} != knowledge.py {emitted} — "
        f"the 3-site contract drifted (变更纪律)"
    )


def test_doc_template_frontmatter_keys_match_contract():
    """distill's doc-template frontmatter keys == the canonical key set."""
    keys = set(_first_frontmatter_keys(DOC_TEMPLATE_MD.read_text(encoding="utf-8")))
    assert keys == EXPECTED_FM_KEYS, f"doc-template frontmatter keys {keys}"


def test_knowledge_reads_every_frontmatter_key(run_script, tmp_path: Path):
    """Behavioral proof that knowledge.py surfaces every non-derived frontmatter
    key into the MEMORY row (so a key documented in doc-template that knowledge
    silently ignored would be caught)."""
    kb = tmp_path / "knowledge-base"
    _write_doc(kb, "cases/x.md", 标题="TITLE_V", 类型="case",
               来源="SRC_V", tags=["TAG_V"], 描述="DESC_V")
    run_script("knowledge.py", "memory-rebuild", "--kb", str(kb))
    mem = (kb / "MEMORY.md").read_text(encoding="utf-8")
    for value in ("TITLE_V", "case", "SRC_V", "TAG_V", "DESC_V"):
        assert value in mem, f"{value} missing from MEMORY row (a frontmatter key was dropped)"
