"""解耦回归:状态根 = workdir、project_root/spec_id 由 flag 驱动、无 .config.json 依赖。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _run(*args, cwd=None, home=None):
    env = os.environ.copy()
    if home:
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
    env.setdefault("PYTHONUTF8", "1")
    cmd = [sys.executable, str(SCRIPTS_DIR / "task_swarm.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=30,
                          cwd=str(cwd) if cwd else None)


def _tasks_md(d: Path) -> Path:
    p = d / "tasks.md"
    p.write_text("## 阶段 1: A\n- [ ] 1.1 任务 @writes:src/f1.py _需求：1.1_\n",
                 encoding="utf-8")
    return p


def test_init_uses_explicit_workdir_for_state_root(tmp_path):
    work = tmp_path / "proj"
    work.mkdir()
    tasks = _tasks_md(tmp_path)            # tasks.md elsewhere; workdir separate
    cp = _run("init", "--tasks", str(tasks), "--workdir", str(work),
              home=tmp_path / "_home")
    assert cp.returncode == 0, cp.stderr
    out = json.loads(cp.stdout)
    run_dir = Path(out["run_dir"])
    assert str(run_dir).startswith(str(work / ".task-swarm" / "runs"))
    assert (run_dir / "state.json").exists()


def test_init_stores_project_root_from_flag(tmp_path):
    work = tmp_path / "proj"
    work.mkdir()
    tasks = _tasks_md(tmp_path)
    pr = tmp_path / "app"
    pr.mkdir()
    cp = _run("init", "--tasks", str(tasks), "--workdir", str(work),
              "--project-root", str(pr), home=tmp_path / "_home")
    assert cp.returncode == 0, cp.stderr
    out = json.loads(cp.stdout)
    state = json.loads((Path(out["run_dir"]) / "state.json").read_text(encoding="utf-8"))
    assert state["project_root"] == str(pr)
    assert state["workdir"] == str(work)
