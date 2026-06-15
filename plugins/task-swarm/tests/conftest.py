"""Shared pytest fixtures for the standalone task-swarm plugin.

Bedrock rules:
  * Tests MUST be hermetic: never read or write the real $HOME.
  * Scripts are invoked as CLIs via subprocess (NOT imported as modules),
    except the pure unit tests that import task_swarm._* directly.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def scripts_dir() -> Path:
    return SCRIPTS_DIR


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect $HOME to tmp_path so Path.home() resolves to an isolated dir."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


@pytest.fixture
def run_script(scripts_dir: Path, fake_home: Path):
    """Run a task-swarm CLI script under the test-controlled environment."""
    def _run(script_name: str, *args: str, stdin: Optional[str] = None,
             cwd: Optional[Path] = None,
             extra_env: Optional[dict] = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["USERPROFILE"] = str(fake_home)
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        if extra_env:
            env.update(extra_env)
        cmd = [sys.executable, str(scripts_dir / script_name), *args]
        return subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", input=stdin if stdin is not None else "",
            env=env, timeout=30, cwd=str(cwd) if cwd else None,
        )
    return _run
