"""Hermetic tests for resolve_root.py (specode 1.0.0 lite)."""
from __future__ import annotations

import json
from pathlib import Path


def _config_path(fake_home: Path) -> Path:
    return fake_home / ".config" / "specode" / "config.json"


def test_get_root_unconfigured_exits_3(run_script, fake_home):
    cp = run_script("resolve_root.py", "get-root")
    assert cp.returncode == 3, cp.stderr
    assert "specsRoot" in (cp.stdout + cp.stderr) or "未配置" in (cp.stdout + cp.stderr)


def test_set_root_persists_to_config(run_script, fake_home, tmp_path):
    target = tmp_path / "my-specs"
    target.mkdir()
    cp = run_script("resolve_root.py", "set-root", "--root", str(target))
    assert cp.returncode == 0, cp.stderr
    cfg = json.loads(_config_path(fake_home).read_text(encoding="utf-8"))
    assert cfg["specsRoot"] == str(target)


def test_set_root_rejects_relative(run_script, fake_home):
    cp = run_script("resolve_root.py", "set-root", "--root", "relative/path")
    assert cp.returncode == 1, cp.stderr


def test_set_root_preserves_other_keys(run_script, fake_home, tmp_path):
    cfgp = _config_path(fake_home)
    cfgp.parent.mkdir(parents=True, exist_ok=True)
    cfgp.write_text(json.dumps({"someOther": "keep-me"}), encoding="utf-8")
    target = tmp_path / "specs2"
    target.mkdir()
    cp = run_script("resolve_root.py", "set-root", "--root", str(target))
    assert cp.returncode == 0, cp.stderr
    cfg = json.loads(cfgp.read_text(encoding="utf-8"))
    assert cfg["someOther"] == "keep-me"
    assert cfg["specsRoot"] == str(target)


def test_get_root_reads_config(run_script, fake_home, tmp_path):
    target = tmp_path / "specs3"
    target.mkdir()
    run_script("resolve_root.py", "set-root", "--root", str(target))
    cp = run_script("resolve_root.py", "get-root")
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == str(target)


def test_get_root_env_beats_config(run_script, fake_home, tmp_path):
    cfg_target = tmp_path / "cfg-specs"
    cfg_target.mkdir()
    run_script("resolve_root.py", "set-root", "--root", str(cfg_target))
    env_target = tmp_path / "env-specs"
    env_target.mkdir()
    cp = run_script("resolve_root.py", "get-root",
                    extra_env={"SPECODE_ROOT": str(env_target)})
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == str(env_target)


def test_list_specs_lists_dirs_with_requirements(run_script, fake_home, tmp_path):
    root = tmp_path / "specs-root"
    (root / "login").mkdir(parents=True)
    (root / "login" / "requirements.md").write_text("# login", encoding="utf-8")
    (root / "payment").mkdir()
    (root / "payment" / "requirements.md").write_text("# payment", encoding="utf-8")
    (root / "not-a-spec").mkdir()  # 只装无关内容、无任何固定产物 → excluded
    (root / "not-a-spec" / "notes.txt").write_text("misc", encoding="utf-8")
    run_script("resolve_root.py", "set-root", "--root", str(root))
    cp = run_script("resolve_root.py", "list-specs")
    assert cp.returncode == 0, cp.stderr
    slugs = set(cp.stdout.split())
    assert slugs == {"login", "payment"}


def test_list_specs_includes_empty_intake_dir(run_script, fake_home, tmp_path):
    # intake 阶段：目录已 mkdir、requirements.md 未写 → 也要在 list 里可见，
    # 与续接表的 intake 状态保持一致。
    root = tmp_path / "specs-root"
    (root / "login").mkdir(parents=True)
    (root / "login" / "requirements.md").write_text("# login", encoding="utf-8")
    (root / "fresh-intake").mkdir()  # 空目录 = intake
    run_script("resolve_root.py", "set-root", "--root", str(root))
    cp = run_script("resolve_root.py", "list-specs")
    assert cp.returncode == 0, cp.stderr
    slugs = set(cp.stdout.split())
    assert slugs == {"login", "fresh-intake"}


def test_list_specs_includes_dir_with_any_fixed_doc(run_script, fake_home, tmp_path):
    # 只有 design.md（无 requirements.md）的目录也是 spec，不应隐身。
    root = tmp_path / "specs-root"
    (root / "half-done").mkdir(parents=True)
    (root / "half-done" / "design.md").write_text("# d", encoding="utf-8")
    run_script("resolve_root.py", "set-root", "--root", str(root))
    cp = run_script("resolve_root.py", "list-specs")
    assert cp.returncode == 0, cp.stderr
    assert set(cp.stdout.split()) == {"half-done"}


def test_list_specs_excludes_hidden_dirs(run_script, fake_home, tmp_path):
    # specsRoot 常是 Obsidian vault 子目录：.obsidian 等隐藏目录（即使为空）不是 spec。
    root = tmp_path / "specs-root"
    (root / ".obsidian").mkdir(parents=True)
    (root / "login").mkdir()
    (root / "login" / "requirements.md").write_text("# login", encoding="utf-8")
    run_script("resolve_root.py", "set-root", "--root", str(root))
    cp = run_script("resolve_root.py", "list-specs")
    assert cp.returncode == 0, cp.stderr
    assert set(cp.stdout.split()) == {"login"}


def test_list_specs_unconfigured_exits_3(run_script, fake_home):
    cp = run_script("resolve_root.py", "list-specs")
    assert cp.returncode == 3, cp.stderr


def test_get_root_flag_beats_env(run_script, fake_home, tmp_path):
    flag_target = tmp_path / "flag-specs"
    flag_target.mkdir()
    cp = run_script("resolve_root.py", "get-root", "--root", str(flag_target),
                    extra_env={"SPECODE_ROOT": str(tmp_path / "env-specs")})
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == str(flag_target)


def test_get_root_unparseable_config_falls_through(run_script, fake_home, tmp_path):
    cfgp = fake_home / ".config" / "specode" / "config.json"
    cfgp.parent.mkdir(parents=True, exist_ok=True)
    cfgp.write_text("42", encoding="utf-8")  # 合法 JSON 但非 dict
    cp = run_script("resolve_root.py", "get-root")
    assert cp.returncode == 3, cp.stderr  # 非 dict → 视为空配置 → 未配置 exit 3


def test_get_root_falls_back_to_legacy_obsidian_root(run_script, fake_home, tmp_path):
    # 1.0.0 前的旧键 obsidianRoot：读端兜底，老用户升级即用
    cfgp = fake_home / ".config" / "specode" / "config.json"
    cfgp.parent.mkdir(parents=True, exist_ok=True)
    legacy = tmp_path / "legacy-specs"
    cfgp.write_text(json.dumps({"obsidianRoot": str(legacy)}), encoding="utf-8")
    cp = run_script("resolve_root.py", "get-root")
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == str(legacy)


def test_get_root_specsroot_beats_legacy_obsidian_root(run_script, fake_home, tmp_path):
    cfgp = fake_home / ".config" / "specode" / "config.json"
    cfgp.parent.mkdir(parents=True, exist_ok=True)
    cfgp.write_text(json.dumps({
        "specsRoot": str(tmp_path / "new-specs"),
        "obsidianRoot": str(tmp_path / "old-specs"),
    }), encoding="utf-8")
    cp = run_script("resolve_root.py", "get-root")
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == str(tmp_path / "new-specs")


# --- design-unchecked (F1: distill should warn if spec not fully executed) ---


def _make_spec(tmp_path: Path, name: str, design_body):
    spec = tmp_path / name
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "requirements.md").write_text("# req\n", encoding="utf-8")
    if design_body is not None:
        (spec / "design.md").write_text(design_body, encoding="utf-8")
    return spec


def test_design_unchecked_all_checked_exits_0(run_script, fake_home, tmp_path):
    spec = _make_spec(tmp_path, "done", "# d\n- [x] a\n  - [x] b\n")
    cp = run_script("resolve_root.py", "design-unchecked", "--spec", str(spec))
    assert cp.returncode == 0, cp.stderr
    assert cp.stdout.strip() == "0"


def test_design_unchecked_counts_unchecked_exits_2(run_script, fake_home, tmp_path):
    spec = _make_spec(tmp_path, "wip", "# d\n- [ ] a\n- [x] b\n  - [ ] c\n")
    cp = run_script("resolve_root.py", "design-unchecked", "--spec", str(spec))
    assert cp.returncode == 2, cp.stderr
    assert cp.stdout.strip() == "2"


def test_design_unchecked_no_design_exits_3(run_script, fake_home, tmp_path):
    spec = _make_spec(tmp_path, "nodesign", None)
    cp = run_script("resolve_root.py", "design-unchecked", "--spec", str(spec))
    assert cp.returncode == 3, cp.stderr
