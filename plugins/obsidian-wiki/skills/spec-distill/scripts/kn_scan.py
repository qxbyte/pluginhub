#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec-distill v2 scan: 比对 SpecIn 下所有 spec 与 vault 内 sync-state 索引，
输出 yml 增量报告。**只读**：scan 不写任何项目目录，仅写 vault 的 report yml。

state 文件由 LLM sync 流程第 6 步追加（见 SKILL.md），本脚本只消费它。

state / report 文件都用 JSON-as-YAML 写：JSON 是 YAML 1.2 的合法子集，既能被
PyYAML 读，也能用 stdlib json 读，零外部依赖。
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
import wikicommon as wc  # noqa: E402


__all__ = [
    "find_specin_root",
    "list_specs",
    "load_state",
    "scan",
    "write_report",
]


# ---------- IO helpers ----------


def load_state(vault, cfg):
    """读 <vault>/00-Index/_system/spec-distill-state.yml；不存在或解析失败返回 {}。

    格式（spec-distill SKILL.md 第 6 步定义）::

        synced:
          <spec_id>:
            project_root: /abs/path
            synced_at: 2026-06-25T16:00:00Z
            new_count: 3
            updated_count: 1
    """
    path = os.path.join(vault, cfg["system_dir"], "spec-distill-state.yml")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.loads(f.read())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    synced = data.get("synced")
    return synced if isinstance(synced, dict) else {}


def write_report(vault, cfg, res):
    """覆盖式写 <vault>/00-Index/_system/spec-distill-report.yml。"""
    path = os.path.join(vault, cfg["system_dir"], "spec-distill-report.yml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


# ---------- discovery ----------


def find_specin_root(vault, cfg):
    """探测 SpecIn / spec-in 等候选目录，返回 vault 相对名；都没有则 None。"""
    for name in cfg["knowledge"]["spec_in_candidates"]:
        if os.path.isdir(os.path.join(vault, name)):
            return name
    return None


def list_specs(vault, source_rel):
    """列出 source_rel 下所有一级目录（每个目录视为一个 spec）。"""
    src = os.path.join(vault, source_rel)
    if not os.path.isdir(src):
        return []
    return sorted(
        name for name in os.listdir(src) if os.path.isdir(os.path.join(src, name))
    )


# ---------- scan ----------


def scan(vault, cfg, source_rel=None):
    if source_rel is None:
        root = find_specin_root(vault, cfg)
        # 正斜杠拼接：Windows 的 os.path / open / listdir 都接受 '/'，
        # 且 report 显示更干净（Obsidian 路径惯例）。
        source_rel = (
            (root + "/" + cfg["knowledge"]["spec_source_default"]) if root else None
        )
    specs = list_specs(vault, source_rel) if source_rel else []
    synced = load_state(vault, cfg)
    synced_ids = set(synced.keys())
    pending = [s for s in specs if s not in synced_ids]
    done_specs = [s for s in specs if s in synced_ids]
    return {
        "schema_version": "1.0",
        "generated_at": _utc_now_isoformat(),
        "source": source_rel,
        "counts": {
            "pending": len(pending),
            "done": len(done_specs),
            "synced_total": len(synced),
        },
        "pending": pending,
        "done": [
            {"spec_id": s, **(synced[s] if isinstance(synced[s], dict) else {})}
            for s in done_specs
        ],
    }


def _utc_now_isoformat():
    """UTC ISO timestamp without microseconds, e.g. ``2026-06-25T16:00:00+00:00``."""
    # datetime.UTC requires Python 3.11+; obsidian-wiki targets 3.8+ via stdlib only,
    # so use the universally available timezone.utc instead.
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


# ---------- CLI ----------


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kn_scan")
    ap.add_argument("command", nargs="?", default="scan", choices=["scan"])
    ap.add_argument(
        "--source",
        default=None,
        help="vault 内相对 spec 源目录（默认按 cfg.spec_in_candidates 自动探测）",
    )
    ap.add_argument("--vault", default=None)
    args = ap.parse_args(argv)
    vault = wc.require_vault(args.vault)
    cfg = wc.load_config(vault)
    res = scan(vault, cfg, args.source)
    rp = write_report(vault, cfg, res)
    print(
        "scan 完成：待沉淀 %d，已沉淀 %d（state 总数 %d）"
        % (res["counts"]["pending"], res["counts"]["done"], res["counts"]["synced_total"])
    )
    print("源：%s" % (res["source"] or "（未找到 SpecIn）"))
    print("报告：%s" % rp)


if __name__ == "__main__":
    main()
