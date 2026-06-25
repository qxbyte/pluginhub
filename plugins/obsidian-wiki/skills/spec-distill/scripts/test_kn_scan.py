# -*- coding: utf-8 -*-
"""Tests for the v2 spec-distill scan script.

v1 read each system's MEMORY.md table to derive coverage; v2 reads a single
vault-side ``00-Index/_system/spec-distill-state.yml`` (JSON-as-YAML) that
the LLM ``sync`` flow appends. These tests cover that contract."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
import wikicommon as wc  # noqa: F401  (kept for symmetry with v1 imports)
import kn_scan as ks


def make_vault(tree):
    root = tempfile.mkdtemp(prefix="sdvault-")
    for rel, content in tree.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return root


def minimal_cfg(**overrides):
    cfg = {
        "system_dir": "00-Index/_system",
        "knowledge": {
            "spec_in_candidates": ["SpecIn", "spec-in"],
            "spec_source_default": "windows-Public/specs",
        },
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


# ---------- discovery ----------


class FindSpecInRootTest(unittest.TestCase):
    def test_specin_picked_first(self):
        v = make_vault({"SpecIn/README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.find_specin_root(v, minimal_cfg()), "SpecIn")

    def test_spec_in_fallback(self):
        v = make_vault({"spec-in/README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.find_specin_root(v, minimal_cfg()), "spec-in")

    def test_uses_cfg_candidates(self):
        v = make_vault({"my-specs/README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        cfg = minimal_cfg(
            knowledge={
                "spec_in_candidates": ["my-specs", "SpecIn"],
                "spec_source_default": "windows-Public/specs",
            }
        )
        self.assertEqual(ks.find_specin_root(v, cfg), "my-specs")

    def test_none_when_missing(self):
        v = make_vault({"README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertIsNone(ks.find_specin_root(v, minimal_cfg()))


class ListSpecsTest(unittest.TestCase):
    def test_lists_top_level_dirs_only(self):
        v = make_vault(
            {
                "SpecIn/windows-Public/specs/REQ-001/requirements.md": "x",
                "SpecIn/windows-Public/specs/REQ-002/requirements.md": "x",
                "SpecIn/windows-Public/specs/REQ-002/sub/extra.md": "x",
                "SpecIn/windows-Public/specs/loose-file.md": "ignored",
            }
        )
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(
            ks.list_specs(v, "SpecIn/windows-Public/specs"),
            ["REQ-001", "REQ-002"],
        )

    def test_missing_source_returns_empty(self):
        v = make_vault({"README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.list_specs(v, "SpecIn/nope"), [])


# ---------- state ----------


class LoadStateTest(unittest.TestCase):
    def test_missing_returns_empty(self):
        v = make_vault({"README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.load_state(v, minimal_cfg()), {})

    def test_parses_json_yaml_state(self):
        state = {
            "synced": {
                "REQ-001": {
                    "project_root": "/abs/path",
                    "synced_at": "2026-06-25T16:00:00+00:00",
                    "new_count": 3,
                },
                "REQ-002": {"project_root": "/abs/other", "synced_at": "2026-06-26T10:00:00+00:00"},
            }
        }
        v = make_vault(
            {"00-Index/_system/spec-distill-state.yml": json.dumps(state, ensure_ascii=False)}
        )
        self.addCleanup(shutil.rmtree, v, True)
        synced = ks.load_state(v, minimal_cfg())
        self.assertEqual(set(synced.keys()), {"REQ-001", "REQ-002"})
        self.assertEqual(synced["REQ-001"]["new_count"], 3)

    def test_corrupt_yaml_returns_empty(self):
        v = make_vault({"00-Index/_system/spec-distill-state.yml": "not: valid: ::: yaml :: !!"})
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.load_state(v, minimal_cfg()), {})

    def test_missing_synced_key_returns_empty(self):
        v = make_vault(
            {"00-Index/_system/spec-distill-state.yml": json.dumps({"other_key": 1})}
        )
        self.addCleanup(shutil.rmtree, v, True)
        self.assertEqual(ks.load_state(v, minimal_cfg()), {})


# ---------- scan ----------


class ScanTest(unittest.TestCase):
    def setUp(self):
        state = json.dumps(
            {
                "synced": {
                    "REQ-114371-脱敏": {
                        "project_root": "/p/a",
                        "synced_at": "2026-06-25T16:00:00+00:00",
                        "new_count": 4,
                    }
                }
            },
            ensure_ascii=False,
        )
        self.v = make_vault(
            {
                "00-Index/_system/spec-distill-state.yml": state,
                "SpecIn/windows-Public/specs/REQ-114371-脱敏/requirements.md": "x",
                "SpecIn/windows-Public/specs/REQ-121659-授权/requirements.md": "x",
                "SpecIn/windows-Public/specs/小程序/design.md": "x",
            }
        )
        self.addCleanup(shutil.rmtree, self.v, True)
        self.cfg = minimal_cfg()

    def test_pending_vs_done_split(self):
        res = ks.scan(self.v, self.cfg)
        self.assertEqual(res["source"], "SpecIn/windows-Public/specs")
        self.assertEqual(res["counts"]["pending"], 2)
        self.assertEqual(res["counts"]["done"], 1)
        self.assertEqual(res["counts"]["synced_total"], 1)
        self.assertEqual(set(res["pending"]), {"REQ-121659-授权", "小程序"})
        done_ids = {d["spec_id"] for d in res["done"]}
        self.assertEqual(done_ids, {"REQ-114371-脱敏"})

    def test_done_carries_state_metadata(self):
        res = ks.scan(self.v, self.cfg)
        done = next(d for d in res["done"] if d["spec_id"] == "REQ-114371-脱敏")
        self.assertEqual(done["project_root"], "/p/a")
        self.assertEqual(done["new_count"], 4)

    def test_no_specin_dir(self):
        v = make_vault({"README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        res = ks.scan(v, self.cfg)
        self.assertIsNone(res["source"])
        self.assertEqual(res["pending"], [])
        self.assertEqual(res["done"], [])
        self.assertEqual(res["counts"]["pending"], 0)

    def test_explicit_source_override(self):
        v = make_vault(
            {
                "SpecIn/other-source/REQ-A/requirements.md": "x",
            }
        )
        self.addCleanup(shutil.rmtree, v, True)
        res = ks.scan(v, self.cfg, "SpecIn/other-source")
        self.assertEqual(res["source"], "SpecIn/other-source")
        self.assertEqual(res["pending"], ["REQ-A"])

    def test_scan_uses_cfg_spec_source_default(self):
        v = make_vault({"SpecIn/custom-source/REQ-A/requirements.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        cfg = minimal_cfg(
            knowledge={
                "spec_in_candidates": ["SpecIn"],
                "spec_source_default": "custom-source",
            }
        )
        res = ks.scan(v, cfg)
        self.assertEqual(res["source"], "SpecIn/custom-source")
        self.assertEqual(res["pending"], ["REQ-A"])

    def test_report_has_schema_version_and_timestamp(self):
        res = ks.scan(self.v, self.cfg)
        self.assertEqual(res["schema_version"], "1.0")
        # ISO format with timezone
        self.assertRegex(res["generated_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


class WriteReportTest(unittest.TestCase):
    def test_writes_yml_as_json(self):
        v = make_vault({"README.md": "x"})
        self.addCleanup(shutil.rmtree, v, True)
        cfg = minimal_cfg()
        res = {
            "schema_version": "1.0",
            "generated_at": "2026-06-25T16:00:00+00:00",
            "source": "SpecIn/windows-Public/specs",
            "counts": {"pending": 1, "done": 0, "synced_total": 0},
            "pending": ["REQ-A"],
            "done": [],
        }
        path = ks.write_report(v, cfg, res)
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            reloaded = json.loads(f.read())
        self.assertEqual(reloaded, res)


if __name__ == "__main__":
    unittest.main()
