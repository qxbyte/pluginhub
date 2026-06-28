"""Regression tests for v0.9 试跑 M8 — SessionStart hook cache vs marketplace drift hint.

试跑结论：merge pluginhub PR 后 host CLI 的 plugin cache 滞后（specode
3.3.0 / task-swarm 0.7.2）而 marketplace.json 已经升到 3.3.1 / 0.7.3 —
本会话直接走 cache 老代码，方案 D 完全不生效；用户/host agent 无感知。

修法：spec_hooks.py SessionStart 增加 _check_plugin_cache_drift() — 解析
__file__ 推 cache 版本 + 找本地 pluginhub git checkout 的 marketplace.json
对照 + diff 时在 additionalContext 末尾加提示。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(REPO_ROOT))

from spec_hooks import (  # noqa: E402
    _check_plugin_cache_drift,
    _detect_cache_version,
    _find_pluginhub_repo,
    _marketplace_version,
)


def _make_marketplace(repo: Path, specode_v: str, taskswarm_v: str = "0.7.4") -> None:
    """Helper: create a minimal marketplace.json in a tmp pluginhub-like dir."""
    (repo / ".claude-plugin").mkdir(parents=True)
    (repo / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {
                "name": "pluginhub",
                "plugins": [
                    {"name": "specode", "version": specode_v, "source": "./plugins/specode"},
                    {"name": "task-swarm", "version": taskswarm_v, "source": "./plugins/task-swarm"},
                ],
            }
        ),
        encoding="utf-8",
    )


def test_detect_cache_version_from_file_path() -> None:
    """When __file__ matches the cache layout, parse out the version."""
    with patch(
        "spec_hooks.__file__",
        "/Users/u/.claude/plugins/cache/pluginhub/specode/3.3.0/scripts/spec_hooks.py",
    ):
        marketplace, plugin, version = _detect_cache_version()
        assert marketplace == "pluginhub"
        assert plugin == "specode"
        assert version == "3.3.0"


def test_detect_cache_version_returns_none_for_non_cache_path() -> None:
    """When loaded via --plugin-dir (no cache path), return all None."""
    with patch(
        "spec_hooks.__file__",
        "/Users/u/Git/pluginhub/plugins/specode/scripts/spec_hooks.py",
    ):
        marketplace, plugin, version = _detect_cache_version()
        assert (marketplace, plugin, version) == (None, None, None)


def test_find_pluginhub_repo_from_env_var(tmp_path: Path) -> None:
    """Env var $PLUGINHUB_REPO_PATH takes priority."""
    repo = tmp_path / "custom-pluginhub"
    _make_marketplace(repo, specode_v="3.3.1")
    with patch.dict("os.environ", {"PLUGINHUB_REPO_PATH": str(repo)}):
        found = _find_pluginhub_repo()
    assert found == repo


def test_find_pluginhub_repo_returns_none_when_nothing(tmp_path: Path, monkeypatch) -> None:
    """No env var, no ~/Git/pluginhub, no ~/pluginhub → None."""
    monkeypatch.delenv("PLUGINHUB_REPO_PATH", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))  # nonexistent paths under tmp
    found = _find_pluginhub_repo()
    assert found is None


def test_marketplace_version_reads_correct_plugin(tmp_path: Path) -> None:
    repo = tmp_path / "pluginhub"
    _make_marketplace(repo, specode_v="3.3.1", taskswarm_v="0.7.4")
    assert _marketplace_version(repo, "specode") == "3.3.1"
    assert _marketplace_version(repo, "task-swarm") == "0.7.4"
    assert _marketplace_version(repo, "nonexistent") is None


def test_marketplace_version_silent_on_missing_file(tmp_path: Path) -> None:
    assert _marketplace_version(tmp_path / "no-such-repo", "specode") is None


def test_check_drift_returns_hint_when_versions_differ(tmp_path: Path) -> None:
    """The integration: cache=3.3.0 + marketplace=3.3.1 → hint string returned."""
    repo = tmp_path / "pluginhub"
    _make_marketplace(repo, specode_v="3.3.1")
    with patch(
        "spec_hooks.__file__",
        "/plugins/cache/pluginhub/specode/3.3.0/scripts/spec_hooks.py",
    ), patch.dict("os.environ", {"PLUGINHUB_REPO_PATH": str(repo)}):
        hint = _check_plugin_cache_drift()
    assert hint is not None
    assert "specode" in hint
    assert "3.3.0" in hint
    assert "3.3.1" in hint
    assert "reload" in hint.lower() or "重启" in hint or "重连" in hint


def test_check_drift_returns_none_when_versions_match(tmp_path: Path) -> None:
    repo = tmp_path / "pluginhub"
    _make_marketplace(repo, specode_v="3.3.0")
    with patch(
        "spec_hooks.__file__",
        "/plugins/cache/pluginhub/specode/3.3.0/scripts/spec_hooks.py",
    ), patch.dict("os.environ", {"PLUGINHUB_REPO_PATH": str(repo)}):
        hint = _check_plugin_cache_drift()
    assert hint is None


def test_check_drift_silent_when_no_cache_path() -> None:
    """--plugin-dir mode (non-cache __file__) → silent (no hint)."""
    with patch(
        "spec_hooks.__file__",
        "/Users/u/Git/pluginhub/plugins/specode/scripts/spec_hooks.py",
    ):
        hint = _check_plugin_cache_drift()
    assert hint is None


def test_check_drift_silent_when_no_local_repo(tmp_path: Path, monkeypatch) -> None:
    """No local pluginhub git checkout → silent (no hint)."""
    monkeypatch.delenv("PLUGINHUB_REPO_PATH", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    with patch(
        "spec_hooks.__file__",
        "/plugins/cache/pluginhub/specode/3.3.0/scripts/spec_hooks.py",
    ):
        hint = _check_plugin_cache_drift()
    assert hint is None


def test_check_drift_silent_on_any_error(tmp_path: Path) -> None:
    """Even if marketplace.json is corrupt, advisory must never throw."""
    repo = tmp_path / "pluginhub"
    (repo / ".claude-plugin").mkdir(parents=True)
    (repo / ".claude-plugin" / "marketplace.json").write_text(
        "{this is not json", encoding="utf-8"
    )
    with patch(
        "spec_hooks.__file__",
        "/plugins/cache/pluginhub/specode/3.3.0/scripts/spec_hooks.py",
    ), patch.dict("os.environ", {"PLUGINHUB_REPO_PATH": str(repo)}):
        # Must not raise; must return None (silent)
        hint = _check_plugin_cache_drift()
    assert hint is None
