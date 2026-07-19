"""Regression tests for v0.12.0 — reviewer change-attribution guard.

Root cause (found in real-machine testing): the reviewer subagent judged "what the
coder changed" from a blind `git status` of the whole working tree, so PRE-EXISTING
uncommitted changes (unrelated to the run) were mis-attributed to the coder as
`@writes`-boundary violations — a false `[contract]` P0 that then escalated to a
p0-fix round targeting a file no coder ever touched.

Fix: `init` snapshots the pre-existing dirty set (`git status --porcelain`) into
state; the reviewer's task.md lists it under 「变更归属」 and is told to attribute
changes via the coder's result.md, excluding the pre-existing set.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from task_swarm._prompt import render_reviewer_prompt  # noqa: E402
from task_swarm._state import StageEntry, StateMachine  # noqa: E402
from task_swarm.cli import _capture_preexisting_dirty  # noqa: E402


def _stage(writes: list[str], number: str = "1.1", title: str = "x") -> StageEntry:
    return StageEntry(
        number=number, title=title,
        items=[{"number": number, "title": title, "writes": writes, "reads": [], "requirements": []}],
        writes=writes, reads=[], requirements=[],
    )


def _render(tmp_path: Path, preexisting_dirty):
    stage = _stage(writes=["src/a.tsx"])
    run_dir = tmp_path / "run"
    return render_reviewer_prompt(
        group_stages=[stage],
        coder_outboxes=[run_dir / "agents" / "coder-g1-s1.1-r1" / "outbox" / "result.md"],
        run_dir=run_dir, run_id="r1", spec_id="s", spec_dir=str(tmp_path / "spec"),
        group="g1", round_=1, project_root=str(tmp_path / "proj"),
        preexisting_dirty=preexisting_dirty,
    )


def test_reviewer_task_md_has_attribution_section(tmp_path: Path) -> None:
    text = _render(tmp_path, ["src/other.tsx", "src/style.css"])
    assert "## 变更归属" in text
    # attribution is via the coder's result.md, not a blind git status
    assert "result.md" in text
    assert "git status" in text  # explicitly told NOT to use it blindly
    # pre-existing dirty files are listed so the reviewer excludes them
    assert "src/other.tsx" in text
    assert "src/style.css" in text


def test_reviewer_clean_tree_fallback_line(tmp_path: Path) -> None:
    text = _render(tmp_path, [])
    assert "## 变更归属" in text
    assert "工作树干净" in text
    text_none = _render(tmp_path, None)
    assert "工作树干净" in text_none


def test_state_roundtrips_preexisting_dirty(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    (run_dir).mkdir()
    sm = StateMachine(run_id="r1", tasks_md="", run_dir=str(run_dir),
                      preexisting_dirty=["src/x.ts", "src/y.ts"])
    sm.save()
    loaded = StateMachine.load(run_dir)
    assert loaded.preexisting_dirty == ["src/x.ts", "src/y.ts"]


def test_capture_preexisting_dirty_non_git_returns_empty(tmp_path: Path) -> None:
    # a plain dir (no git) → graceful empty, no error
    assert _capture_preexisting_dirty(str(tmp_path)) == []
    # None project_root → empty
    assert _capture_preexisting_dirty(None) == []


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_capture_preexisting_dirty_finds_dirty_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "committed.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
    # now make the tree dirty: modify a tracked file + add an untracked one
    (repo / "committed.txt").write_text("v2\n", encoding="utf-8")
    (repo / "new.txt").write_text("x\n", encoding="utf-8")

    dirty = _capture_preexisting_dirty(str(repo))
    assert "committed.txt" in dirty
    assert "new.txt" in dirty
