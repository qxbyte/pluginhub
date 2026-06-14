"""tests for task_swarm/_pipeline_yaml.py — pipeline.yml YAML-subset parser."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from task_swarm._pipeline_yaml import parse, PipelineYamlError  # noqa: E402


# --- Step A: block map + scalars ---

def test_flat_map_scalars():
    text = "version: 1\nname: hello\nflag: true\nempty:\n"
    assert parse(text) == {"version": 1, "name": "hello", "flag": True, "empty": None}


def test_nested_map():
    text = "run:\n  spec_id: user-login\n  max_parallel: 4\n"
    assert parse(text) == {"run": {"spec_id": "user-login", "max_parallel": 4}}


def test_bool_only_true_false_not_yes():
    assert parse("a: yes\nb: no\nc: on\n") == {"a": "yes", "b": "no", "c": "on"}
