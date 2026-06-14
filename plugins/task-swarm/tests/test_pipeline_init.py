import json, os, subprocess, sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

def _run(*args, cwd=None, home=None):
    env = os.environ.copy()
    if home:
        env["HOME"] = str(home); env["USERPROFILE"] = str(home)
    env.setdefault("PYTHONUTF8", "1")
    cmd = [sys.executable, str(SCRIPTS_DIR / "task_swarm.py"), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=30,
                          cwd=str(cwd) if cwd else None)

_YML = ('version: 1\nrun:\n  max_parallel: 4\ntask_groups:\n'
        '  - id: g1\n    name: A\n    tasks:\n      - id: g1.1\n        title: alpha\n'
        '        writes: [src/a.py]\n        requirements: ["1.1"]\n')

def _write_yml(d: Path) -> Path:
    p = d / "pipeline.yml"; p.write_text(_YML, encoding="utf-8"); return p

def test_init_pipeline_builds_state(tmp_path):
    work = tmp_path / "proj"; work.mkdir()
    yml = _write_yml(tmp_path)
    cp = _run("init", "--pipeline", str(yml), "--workdir", str(work), home=tmp_path / "_home")
    assert cp.returncode == 0, cp.stderr
    out = json.loads(cp.stdout)
    run_dir = Path(out["run_dir"])
    assert (run_dir / "state.json").exists()
    assert (run_dir / "pipeline.yml").exists()
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    assert state["pipeline_path"].endswith("pipeline.yml")
    assert len(state["groups"]) >= 1

def test_init_pipeline_then_plan_runs(tmp_path):
    work = tmp_path / "proj"; work.mkdir()
    yml = _write_yml(tmp_path)
    init = json.loads(_run("init", "--pipeline", str(yml), "--workdir", str(work),
                           home=tmp_path / "_home").stdout)
    cp = _run("plan", "--run", init["run_id"], cwd=work, home=tmp_path / "_home")
    assert cp.returncode == 0, cp.stderr
    plan = json.loads(cp.stdout)
    assert plan["phase"] in ("coding", "init")
    assert plan.get("action") in ("coding-fork", None) or plan.get("fork") is not None
