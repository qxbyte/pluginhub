#!/usr/bin/env python3
"""spec_hooks.py — specode lite's only hook: SessionStart discipline injection.

Reads stdin (tolerates non-TTY / empty), emits additionalContext JSON to stdout, exit 0.
Swallows any exception and exits 0 (advisory, never blocks).

Multi-host: this one handler serves every supported host. It emits the nested
`hookSpecificOutput.additionalContext` shape, which Claude Code, CodeBuddy, and Codex
all consume for SessionStart; it reads no `*_PLUGIN_ROOT` env var (the drift check keys
off `__file__`), so it does not care which host launched it. The per-host difference is
only in the hooks manifest that invokes this script — `hooks/hooks.json`
(`${CLAUDE_PLUGIN_ROOT}`), `hooks/hooks.codebuddy.json` (`${CODEBUDDY_PLUGIN_ROOT}`),
`hooks/hooks.codex.json` (`${PLUGIN_ROOT}`, matcher `startup|resume|clear`) — so there
is no output-format branching to add here.

v0.9 trial M8: adds a silent _check_plugin_cache_drift() — parses __file__ to infer the
currently cache-loaded version, compares against the local pluginhub git repo's (if present)
marketplace.json latest version, and on a diff appends a hint to additionalContext telling the
user to reload. No network access; if marketplace.json is unreachable, skip silently.

Note: the emitted DISCIPLINE reminder and the drift-hint message stay Chinese (user-facing output).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DISCIPLINE = (
    "specode（spec-mode 轻量工作流）可用。仅在用户输入 `/specode:spec <需求>`、"
    "`/specode:continue <slug>`、`/specode:execute <slug>`、`/specode:list` "
    "或显式要求用 spec 模式时激活；否则按普通对话处理。"
    "激活后遵循对应命令 skill（spec / continue / execute / list）"
    "：① requirements 由 specode:intake skill 产（项目分析+澄清+写需求）；"
    "design/tasks 各 phase 优先调对应 superpowers skill（缺席则 specode-native 降级）；"
    "② 4 份固定产物 requirements.md / design.md / tasks.md / implementation-log.md 永远以固定文件名"
    "落在 <specsRoot>/<slug>/；③ tasks 完成后由 specode:execute skill 承接执行尾段"
    "（执行方式 selector → 执行 → 验收 → distill 提示），也可随时手动 `/specode:execute <slug>` 触发。"
)


_CACHE_PATH_RE = re.compile(
    r"/plugins/cache/(?P<marketplace>[^/]+)/(?P<plugin>[^/]+)/(?P<version>[^/]+)/"
)


def _detect_cache_version() -> tuple[str | None, str | None, str | None]:
    """Parse this script's __file__ to figure out which cache version is loaded.

    Returns (marketplace_name, plugin_name, version_str) or (None, None, None)
    when the path doesn't match the host-CLI cache layout (typical for `--plugin-dir`
    local-checkout runs — there is no drift to check in that case).
    """
    try:
        m = _CACHE_PATH_RE.search(__file__)
    except (NameError, TypeError):
        return None, None, None
    if not m:
        return None, None, None
    return m.group("marketplace"), m.group("plugin"), m.group("version")


def _find_pluginhub_repo() -> Path | None:
    """Find the local pluginhub git checkout, if any.

    Priority:
      1. ``$PLUGINHUB_REPO_PATH`` env var (explicit override)
      2. ``~/Git/pluginhub`` (xueqiang convention; matches the dev box layout)
      3. ``~/pluginhub``
    Returns the absolute path if the directory contains
    ``.claude-plugin/marketplace.json``, else None.
    """
    candidates: list[Path] = []
    env = os.environ.get("PLUGINHUB_REPO_PATH")
    if env:
        candidates.append(Path(env).expanduser())
    home = Path.home()
    candidates.extend([home / "Git" / "pluginhub", home / "pluginhub"])
    for c in candidates:
        try:
            mf = c / ".claude-plugin" / "marketplace.json"
            if mf.is_file():
                return c
        except OSError:
            continue
    return None


def _marketplace_version(repo: Path, plugin_name: str) -> str | None:
    """Read marketplace.json and return the version pinned for ``plugin_name``,
    or None if anything fails (advisory — never throws)."""
    try:
        mf = repo / ".claude-plugin" / "marketplace.json"
        data = json.loads(mf.read_text(encoding="utf-8"))
        for p in data.get("plugins", []):
            if isinstance(p, dict) and p.get("name") == plugin_name:
                v = p.get("version")
                return v if isinstance(v, str) else None
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return None


def _check_plugin_cache_drift() -> str | None:
    """Return a one-paragraph advisory if cache version != marketplace version.

    Returns None when:
      - this script isn't running from a cache path (e.g. --plugin-dir mode)
      - no local pluginhub git checkout to compare against
      - cache and marketplace agree
      - any error (silent — advisory must never noise)
    """
    try:
        _, plugin_name, cache_version = _detect_cache_version()
        if not plugin_name or not cache_version:
            return None
        repo = _find_pluginhub_repo()
        if repo is None:
            return None
        market_version = _marketplace_version(repo, plugin_name)
        if not market_version or market_version == cache_version:
            return None
        return (
            f"\n\n⚠ specode cache drift detected: 本会话用的是 cache 版本 "
            f"`{plugin_name} {cache_version}`，但本地 pluginhub git 仓库的 "
            f"marketplace.json 已 pin 到 `{market_version}`。两者不一致——"
            f"如果你刚 merge pluginhub PR 想验新行为，**必须 reload 宿主 CLI "
            f"（重启 / 重连 session）** 让 host CLI 重新拉 cache，否则本会话仍跑旧代码。"
            f"（路径：{repo}/.claude-plugin/marketplace.json；设 `PLUGINHUB_REPO_PATH` "
            f"env var 可指向别处的 checkout）"
        )
    except Exception:
        return None


def main() -> int:
    try:
        try:
            sys.stdin.read()
        except Exception:
            pass
        context = DISCIPLINE
        drift_hint = _check_plugin_cache_drift()
        if drift_hint:
            context = context + drift_hint
        out = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
