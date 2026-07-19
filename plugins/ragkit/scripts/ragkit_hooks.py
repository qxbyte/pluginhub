#!/usr/bin/env python3
"""ragkit_hooks.py — RagKit's only hook: SessionStart bootstrap injection.

Reads stdin (tolerates non-TTY / empty), emits an additionalContext JSON to
stdout, exit 0. Swallows any exception and exits 0 (advisory, never blocks).

Why this exists: on harnesses like CodeBuddy a plugin's skills stay INERT
without a session-start bootstrap — they don't surface as commands and the
model won't reach for them (superpowers' porting guide: "the bootstrap is the
entire integration; without it the skill files are inert"). Some hosts (e.g.
Claude Code) natively discover plugin skills, so RagKit worked there without a
hook; other harnesses need this. Mirrors specode's spec_hooks.py emit shape (proven on the
same setup). The bootstrap also carries the hard guardrail that stops a weak
model from bypassing the plugin and hand-rolling retrieval.
"""
from __future__ import annotations

import json
import sys

BOOTSTRAP = (
    "RagKit 可用：对项目 `knowledge-base/` 做多路检索（向量+词汇+元数据，RRF 融合）。"
    "四个 skill —— `ragkit:query`（检索，返回定位卡片）/ `ragkit:embed`（构建/更新向量索引）"
    "/ `ragkit:status`（索引健康）/ `ragkit:eval`（检索精度评估）。用户要检索 / 建索引 / 查健康时，"
    "用 `Skill` 工具（或宿主等价的 skill 调用机制）**按名调用**对应 skill（`/ragkit:*` 或直接按名，无需去找命令文件）。"
    "硬约束（防脱轨）：① 只按名调 skill，**绝不在文件系统里搜 skill / 脚本文件**——"
    "插件文件在插件缓存目录、不在你的项目里，skill 内部会自己定位脚本；"
    "② 检索**只能**调 RagKit 的脚本，**严禁**自己读 `.ragkit` 向量文件、装 numpy、"
    "或用 embedding API 手搓相似度（结果会错且不可复现）；"
    "③ 脚本定位 / 运行失败 → 停下报确切错误，不要绕过、不要自己实现。"
)


def main() -> int:
    try:
        try:
            sys.stdin.read()
        except Exception:
            pass
        out = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": BOOTSTRAP,
            }
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
