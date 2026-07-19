#!/usr/bin/env python3
"""Verify every host manifest's plugin versions stay in lockstep.

Why this script exists (AI-EDS v0.9 痛点 #4)
-------------------------------------------------
pluginhub ships each plugin to several host CLIs (Claude Code / CodeBuddy /
Codex / Kimi). Each host reads its **own** manifest set:

  host        per-plugin manifest                 root catalog
  ---------   ---------------------------------   ------------------------------------
  claude      <plugin>/.claude-plugin/plugin.json  .claude-plugin/marketplace.json
  codebuddy   <plugin>/.codebuddy-plugin/plugin.json  .codebuddy-plugin/marketplace.json
  codex       <plugin>/.codex-plugin/plugin.json   .agents/plugins/marketplace.json
  kimi        <plugin>/.kimi-plugin/plugin.json    .kimi-plugin/marketplace.json

The catalog a host reads must mirror that host's plugin.json version, and every
host must agree on a single version per plugin — otherwise a host shows / installs
a stale build even though the repo tree has the new code. This drift bit us for
real on 2026-06-28 (marketplace.json had specode=2.0.0 while the plugin was 3.1.0),
before the multi-host split even existed; adding three more host manifests
multiplies the ways it can silently widen.

The **canonical** version of a plugin is its `.claude-plugin/plugin.json` version.
Every other host manifest (per-plugin plugin.json + that host's catalog entry) must
equal it. This script runs in CI on every PR / push and exits 1 on any drift or any
missing host manifest — full multi-host coverage is enforced, not optional.

Stdlib-only (no PyYAML / no third party). Safe to run on any Python 3.8+.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# host key -> (per-plugin manifest dir, root catalog path relative to ROOT)
HOSTS: dict[str, tuple[str, str]] = {
    "claude": (".claude-plugin", ".claude-plugin/marketplace.json"),
    "codebuddy": (".codebuddy-plugin", ".codebuddy-plugin/marketplace.json"),
    "codex": (".codex-plugin", ".agents/plugins/marketplace.json"),
    "kimi": (".kimi-plugin", ".kimi-plugin/marketplace.json"),
}

CANONICAL_HOST = "claude"


def _read_version(path: Path) -> str | None:
    """Return the top-level `version` string from a JSON manifest, or None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    v = data.get("version")
    return v if isinstance(v, str) else None


def _read_catalog(path: Path) -> dict[str, str]:
    """Return {plugin_name: version} from a marketplace/catalog JSON."""
    out: dict[str, str] = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return out
    for entry in data.get("plugins") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        version = entry.get("version")
        if isinstance(name, str) and isinstance(version, str):
            out[name] = version
    return out


def _plugin_names() -> list[str]:
    """Every directory under plugins/ that carries a .claude-plugin/plugin.json."""
    names: list[str] = []
    for plugin_dir in sorted((ROOT / "plugins").iterdir()):
        if (plugin_dir / ".claude-plugin" / "plugin.json").is_file():
            names.append(plugin_dir.name)
    return names


def main() -> int:
    errors: list[str] = []
    plugins = _plugin_names()

    # Canonical version per plugin = its .claude-plugin/plugin.json version.
    canonical: dict[str, str] = {}
    for name in plugins:
        v = _read_version(ROOT / "plugins" / name / ".claude-plugin" / "plugin.json")
        if v is None:
            errors.append(f"plugins/{name}/.claude-plugin/plugin.json missing a version")
        else:
            canonical[name] = v

    for host, (mdir, catalog_rel) in HOSTS.items():
        # 1. Each plugin's per-host plugin.json must exist and match canonical.
        for name in plugins:
            manifest = ROOT / "plugins" / name / mdir / "plugin.json"
            if not manifest.is_file():
                errors.append(
                    f"[{host}] plugins/{name}/{mdir}/plugin.json is missing "
                    f"(every plugin must carry all {len(HOSTS)} host manifests)"
                )
                continue
            v = _read_version(manifest)
            if v is None:
                errors.append(f"[{host}] plugins/{name}/{mdir}/plugin.json missing a version")
            elif name in canonical and v != canonical[name]:
                errors.append(
                    f"[{host}] version drift for {name}: {mdir}/plugin.json says {v}, "
                    f"canonical (.claude-plugin) says {canonical[name]}"
                )

        # 2. That host's root catalog must exist, list every plugin, and match canonical.
        catalog_path = ROOT / catalog_rel
        if not catalog_path.is_file():
            errors.append(f"[{host}] root catalog {catalog_rel} is missing")
            continue
        catalog = _read_catalog(catalog_path)
        for name in plugins:
            if name not in catalog:
                errors.append(f"[{host}] {catalog_rel} does not list {name}")
            elif name in canonical and catalog[name] != canonical[name]:
                errors.append(
                    f"[{host}] version drift for {name}: {catalog_rel} says {catalog[name]}, "
                    f"canonical (.claude-plugin) says {canonical[name]}"
                )
        for name in sorted(set(catalog) - set(plugins)):
            errors.append(
                f"[{host}] {catalog_rel} lists {name}@{catalog[name]} "
                f"but plugins/{name}/ does not exist"
            )

    if errors:
        sys.stderr.write("❌ host manifests out of sync:\n\n")
        for e in errors:
            sys.stderr.write(f"  • {e}\n")
        sys.stderr.write(
            "\nFix: bump every host manifest for the plugin to one version — the "
            "per-plugin plugin.json under each of "
            + " / ".join(sorted({d for d, _ in HOSTS.values()}))
            + " and each host's root catalog "
            + " / ".join(sorted({c for _, c in HOSTS.values()}))
            + ".\nThe .claude-plugin/plugin.json version is canonical.\n"
        )
        return 1

    print(
        f"✓ {len(plugins)} plugin(s) in lockstep across {len(HOSTS)} host(s) "
        f"({', '.join(sorted(HOSTS))}):"
    )
    for name in plugins:
        print(f"  - {name} @ {canonical.get(name, '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
