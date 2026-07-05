#!/usr/bin/env python3
"""resolve_root.py — specsRoot resolution + persistence for specode lite (stdlib-only).

verbs:
  get-root  [--root P]   resolve specsRoot: --root > env SPECODE_ROOT > config.specsRoot
  set-root  --root P     absolute path, persisted to ~/.config/specode/config.json.specsRoot
  list-specs [--root P]  list spec dir names under root (one slug per line): subdirs
                         containing any fixed doc (requirements/design/tasks/implementation-log.md),
                         or empty subdirs (intake: dir created, requirements not yet written);
                         hidden dirs excluded
  resolve-project-root [--cwd P]   compute the project_root default (git toplevel || cwd),
                                   for the host agent to confirm via AskUserQuestion
  write-project-root --spec P --root A   write project_root into a spec's requirements.md
                                   frontmatter (single writer; validates absolute / dir exists / mount)
  read-project-root  --spec P      read project_root from a spec's requirements.md frontmatter
                                   (the single reader for all downstream; missing field exit 3 / invalid exit 4)

project_root is the sole join key between a spec (under specsRoot) and its target project, stored
in exactly ONE place — that spec's requirements.md YAML frontmatter. write/read are its only
write/read entry points, preventing the split-brain of each step deriving it from cwd/workdir.

exit codes: 0 ok / 1 usage or argument error / 3 unconfigured (specsRoot unset / project_root field missing)
            / 4 project_root value invalid (non-absolute / dir missing / external drive not mounted)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "specode"


def _config_path() -> Path:
    return _config_dir() / "config.json"


def _read_config() -> dict:
    p = _config_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1  # fdopen takes over the fd
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.remove(tmp)


def _resolve(root_flag):
    if root_flag:
        return root_flag
    env = os.environ.get("SPECODE_ROOT")
    if env:
        return env
    cfg = _read_config()
    # specsRoot is the current key; obsidianRoot is the pre-1.0.0 legacy key — the read side
    # falls back to it so upgrading users keep working without re-setting.
    val = cfg.get("specsRoot") or cfg.get("obsidianRoot")
    return val or None


def cmd_get_root(args) -> int:
    root = _resolve(args.root)
    if not root:
        sys.stderr.write(
            "specode: specsRoot 未配置。请先用 set-root 设置，或设 env SPECODE_ROOT。\n")
        return 3
    sys.stdout.write(root + "\n")
    return 0


def cmd_set_root(args) -> int:
    p = args.root
    if not os.path.isabs(p):
        sys.stderr.write(f"specode: 根目录必须是绝对路径，收到：{p}\n")
        return 1
    cfg = _read_config()
    cfg["specsRoot"] = p
    # v0.9 pain point #8: drop the legacy `obsidianRoot` key so downstream plugins
    # that still read it (obsidian-wiki etc.) don't see a stale path after
    # the user moves their vault. The read-side already falls back from
    # specsRoot to obsidianRoot, so leaving both in the JSON silently created
    # split-brain in real use (incident 2026-06-28).
    cfg.pop("obsidianRoot", None)
    _atomic_write_json(_config_path(), cfg)
    sys.stdout.write(f"specode: 已设 specsRoot = {p}\n")
    return 0


_FIXED_DOCS = ("requirements.md", "design.md", "tasks.md", "implementation-log.md")


def _is_spec_dir(child: Path) -> bool:
    """Has any fixed doc → spec; empty dir → intake spec (dir created, requirements not yet written).
    A dir holding only unrelated content (e.g. attachments/) is not a spec."""
    if any((child / doc).exists() for doc in _FIXED_DOCS):
        return True
    try:
        next(child.iterdir())
    except StopIteration:
        return True  # empty dir = intake
    except OSError:
        return False
    return False


def cmd_list_specs(args) -> int:
    root = _resolve(args.root)
    if not root:
        sys.stderr.write("specode: specsRoot 未配置。\n")
        return 3
    base = Path(root)
    if not base.is_dir():
        return 0  # configured but the dir doesn't exist yet → empty list
    for child in sorted(base.iterdir()):
        if child.name.startswith("."):
            continue  # hidden dirs like .obsidian / .git are not specs
        if child.is_dir() and _is_spec_dir(child):
            sys.stdout.write(child.name + "\n")
    return 0


# ---------- project_root: single source of truth (FIX-1) ----------


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1  # fdopen takes over the fd
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if os.path.exists(tmp):
            os.remove(tmp)


def _requirements_path(spec: str) -> Path:
    """Resolve the requirements.md for a spec given a dir or a file path."""
    p = Path(spec)
    if p.is_dir():
        return p / "requirements.md"
    return p


def _design_path(spec: str) -> Path:
    """Resolve the design.md for a spec given a dir or a file path."""
    p = Path(spec)
    if p.is_dir():
        return p / "design.md"
    return p


def _tasks_path(spec: str) -> Path:
    """Resolve the tasks.md for a spec given a dir or a file path."""
    p = Path(spec)
    if p.is_dir():
        return p / "tasks.md"
    return p


def _split_frontmatter(text: str):
    """Return ``(fm_lines | None, body)``.

    fm_lines is the list of YAML frontmatter lines between the leading
    ``---`` and its terminator; ``None`` when the file has no (well-formed)
    frontmatter. body is everything after the closing ``---``.
    """
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = lines[1:i]
            body = "\n".join(lines[i + 1 :])
            return fm, body
    return None, text  # unterminated frontmatter → treat as none


def _fm_get(fm_lines: list[str], key: str):
    prefix = key + ":"
    for line in fm_lines:
        if line.startswith(prefix):
            val = line[len(prefix) :].strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in {'"', "'"}:
                val = val[1:-1]
            return val
    return None


def _fm_set(fm_lines: list[str], key: str, value: str) -> list[str]:
    prefix = key + ":"
    out: list[str] = []
    found = False
    for line in fm_lines:
        if line.startswith(prefix):
            out.append(f"{key}: {value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}: {value}")
    return out


def _validate_root(p: str) -> tuple[bool, str]:
    """Return ``(ok, message)`` for a candidate project_root absolute path.

    Checks: absolute · (if under /Volumes) the mount point exists · the
    directory exists. No silent fallback — callers map failure to their own
    exit code (write → 1, read → 4).
    """
    if not os.path.isabs(p):
        return False, f"project_root 必须是绝对路径，收到：{p}"
    if p.startswith("/Volumes/"):
        parts = p.split("/")
        if len(parts) >= 3 and parts[2]:
            mount = "/Volumes/" + parts[2]
            if not os.path.isdir(mount):
                return False, f"外置盘未挂载：{mount}（拒绝写到/读自未挂载路径）"
    if not os.path.isdir(p):
        return False, f"project_root 目录不存在：{p}"
    return True, ""


def cmd_resolve_project_root(args) -> int:
    cwd = args.cwd or os.getcwd()
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            sys.stdout.write(out.stdout.strip() + "\n")
            return 0
    except (OSError, subprocess.SubprocessError):
        pass
    sys.stdout.write(os.path.abspath(cwd) + "\n")
    return 0


def cmd_write_project_root(args) -> int:
    root = args.root
    ok, msg = _validate_root(root)
    if not ok:
        sys.stderr.write(f"specode: {msg}\n")
        return 1
    req = _requirements_path(args.spec)
    if not req.is_file():
        # allow an upper layer to create requirements.md first; require the file to exist
        # here so we don't write to the wrong place
        sys.stderr.write(f"specode: 找不到 requirements.md：{req}\n")
        return 1
    text = req.read_text(encoding="utf-8")
    fm_lines, body = _split_frontmatter(text)
    if fm_lines is None:
        new_text = "---\n" + f"project_root: {root}" + "\n---\n" + text
    else:
        fm_lines = _fm_set(fm_lines, "project_root", root)
        new_text = "---\n" + "\n".join(fm_lines) + "\n---\n" + body
    _atomic_write_text(req, new_text)
    sys.stdout.write(f"specode: 已写 project_root = {root} 到 {req}\n")
    return 0


def cmd_read_project_root(args) -> int:
    req = _requirements_path(args.spec)
    if not req.is_file():
        sys.stderr.write(
            f"specode: 找不到 requirements.md：{req}（无法解析 project_root）\n"
        )
        return 3
    text = req.read_text(encoding="utf-8")
    fm_lines, _ = _split_frontmatter(text)
    value = _fm_get(fm_lines, "project_root") if fm_lines is not None else None
    if not value:
        sys.stderr.write(
            "specode: requirements.md 缺 project_root frontmatter；"
            "specode v2.0 之前生成的 spec 需先补字段后重试。\n"
        )
        return 3
    ok, msg = _validate_root(value)
    if not ok:
        sys.stderr.write(f"specode: {msg}\n")
        return 4
    sys.stdout.write(value + "\n")
    return 0


def cmd_plan_unchecked(args) -> int:
    """count unchecked ``- [ ]`` steps in a spec's executable plan.

    6.0.0: the plan lives in tasks.md; 5.x legacy specs carry it in
    design.md (detected by checkbox lines). distill uses this to warn
    before sedimenting an unfinished spec (knowledge points must not
    reference planned-but-unbuilt code).

    exit 0 — plan exists and every checkbox is checked (executed)
    exit 2 — plan exists with N>0 unchecked ``- [ ]`` (prints N)
    exit 3 — no plan (no tasks.md; design.md absent or has no checkboxes)
    """
    target = _tasks_path(args.spec)
    if not target.is_file():
        d = _design_path(args.spec)
        if d.is_file() and any(
            line.lstrip().startswith(("- [ ]", "- [x]"))
            for line in d.read_text(encoding="utf-8").splitlines()
        ):
            target = d  # 5.x legacy spec: design.md is the plan
        else:
            sys.stderr.write(
                f"specode: 找不到可执行计划（无 tasks.md，"
                f"design.md 缺失或不含 checkbox）：{args.spec}\n")
            return 3
    n = 0
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("- [ ]"):
            n += 1
    sys.stdout.write(f"{n}\n")
    return 2 if n > 0 else 0


_DEFAULTS_SCHEMA = {
    # key: (type, default, env_var_name)
    "interactive": (bool, True, "SPECODE_INTERACTIVE"),
    "project_root_default": (str, None, "SPECODE_PROJECT_ROOT"),
    "execution_mode_default": (str, "ask", "SPECODE_EXECUTION_MODE"),
    "auto_distill": (bool, True, "SPECODE_AUTO_DISTILL"),
    "specs_root_default": (str, None, "SPECODE_SPECS_ROOT_DEFAULT"),
}

_VALID_EXECUTION_MODES = {
    "ask", "task-swarm", "superpowers-subagent",
    "superpowers-executing", "specode-self",
}


def _defaults_path() -> Path:
    """Per-user defaults file. Separate from config.json so specsRoot
    setup (one-time, persistent across all sessions) stays untangled
    from the per-flow autonomous-mode defaults (rarely changed but
    sometimes set per CI run via env var)."""
    return _config_dir() / "defaults.json"


def _read_defaults() -> dict:
    p = _defaults_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _coerce_value(raw, expected_type):
    """Convert raw env var / CLI string to typed value. Raises ValueError
    on invalid input — caller decides whether to err out or silently skip."""
    if expected_type is bool:
        if isinstance(raw, bool):
            return raw
        if not isinstance(raw, str):
            raise ValueError(f"bool expected, got {type(raw).__name__}: {raw!r}")
        low = raw.strip().lower()
        if low in ("true", "1", "yes", "on"):
            return True
        if low in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"bool expected, got: {raw!r}")
    if expected_type is str:
        return str(raw) if raw is not None else None
    raise ValueError(f"unsupported type: {expected_type}")


def _effective_default(key: str) -> tuple[object, str]:
    """Resolve effective value for a defaults key.

    Priority: env var > defaults.json > schema default.
    Returns (value, source) — source ∈ {"env", "file", "default"}.
    Invalid env value silently falls through to file/default (advisory:
    user should re-export with valid value if they care).
    """
    if key not in _DEFAULTS_SCHEMA:
        raise KeyError(f"unknown defaults key: {key!r}")
    expected_type, schema_default, env_name = _DEFAULTS_SCHEMA[key]

    env_raw = os.environ.get(env_name)
    if env_raw is not None and env_raw != "":
        try:
            return _coerce_value(env_raw, expected_type), "env"
        except ValueError:
            pass  # fall through to file/default

    file_data = _read_defaults()
    if key in file_data:
        try:
            return _coerce_value(file_data[key], expected_type), "file"
        except ValueError:
            pass

    return schema_default, "default"


def cmd_read_defaults(args) -> int:
    """v0.9 M1/M9 (3.4.0): read autonomous-mode defaults.

    --key <name>  Single key, print value (with --json prints {value, source}).
    (no --key)    All keys as JSON map.

    Resolution: env var > defaults.json > schema default.
    Unknown key → exit 1.
    """
    if getattr(args, "key", None):
        if args.key not in _DEFAULTS_SCHEMA:
            sys.stderr.write(
                f"specode: unknown defaults key {args.key!r}. "
                f"Valid keys: {', '.join(sorted(_DEFAULTS_SCHEMA))}\n"
            )
            return 1
        value, source = _effective_default(args.key)
        if getattr(args, "json", False):
            sys.stdout.write(json.dumps({"key": args.key, "value": value,
                                          "source": source}) + "\n")
        else:
            # Plain text — bool as "true"/"false", None as empty line.
            if value is None:
                sys.stdout.write("\n")
            elif isinstance(value, bool):
                sys.stdout.write("true\n" if value else "false\n")
            else:
                sys.stdout.write(str(value) + "\n")
        return 0

    # All keys
    out = {}
    for key in _DEFAULTS_SCHEMA:
        value, source = _effective_default(key)
        out[key] = {"value": value, "source": source}
    sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    return 0


def cmd_write_default(args) -> int:
    """v0.9 M1/M9 (3.4.0): persist a defaults key to ~/.config/specode/defaults.json.

    Validates against the schema (key name + value type). Doesn't touch
    env vars — env always wins.
    """
    key = args.key
    if key not in _DEFAULTS_SCHEMA:
        sys.stderr.write(
            f"specode: unknown defaults key {key!r}. "
            f"Valid keys: {', '.join(sorted(_DEFAULTS_SCHEMA))}\n"
        )
        return 1
    expected_type, _, _ = _DEFAULTS_SCHEMA[key]
    try:
        value = _coerce_value(args.value, expected_type)
    except ValueError as exc:
        sys.stderr.write(f"specode: invalid value for {key!r}: {exc}\n")
        return 1
    # execution_mode_default whitelist
    if key == "execution_mode_default" and value not in _VALID_EXECUTION_MODES:
        sys.stderr.write(
            f"specode: execution_mode_default must be one of: "
            f"{', '.join(sorted(_VALID_EXECUTION_MODES))}; got {value!r}\n"
        )
        return 1
    data = _read_defaults()
    data[key] = value
    _atomic_write_json(_defaults_path(), data)
    sys.stdout.write(f"specode: defaults.{key} = {json.dumps(value)}\n")
    return 0


def cmd_reset_default(args) -> int:
    """v0.9 M1/M9 (3.4.0): remove a defaults key (or all when --all)."""
    if getattr(args, "all", False):
        path = _defaults_path()
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                sys.stderr.write(f"specode: failed to remove {path}: {exc}\n")
                return 1
        sys.stdout.write("specode: all defaults reset (file removed)\n")
        return 0
    if not getattr(args, "key", None):
        sys.stderr.write("specode: pass --key <name> or --all\n")
        return 1
    if args.key not in _DEFAULTS_SCHEMA:
        sys.stderr.write(f"specode: unknown defaults key {args.key!r}\n")
        return 1
    data = _read_defaults()
    if args.key in data:
        del data[args.key]
        _atomic_write_json(_defaults_path(), data)
    sys.stdout.write(f"specode: defaults.{args.key} reset\n")
    return 0


def cmd_doctor(args) -> int:
    """v0.9 pain point #9: surface config drift early.

    Exit codes mirror the read-project-root convention so scripts can
    branch deterministically:
      0 — specsRoot configured + directory exists (may print warnings)
      3 — specsRoot not configured at all
      4 — specsRoot configured but directory missing (e.g. user renamed /
          unmounted external drive)
    """
    cfg = _read_config()
    legacy = cfg.get("obsidianRoot")
    specs_root = cfg.get("specsRoot") or legacy
    config_file = _config_path()

    if not specs_root:
        sys.stderr.write(
            "specode doctor: specsRoot 未配置。\n"
            "  Fix: resolve_root.py set-root --root <abs-path-to-specs-dir>\n"
        )
        return 3

    if not os.path.isdir(specs_root):
        sys.stderr.write(
            f"specode doctor: specsRoot 指向的目录不存在或不可访问\n"
            f"  current value: {specs_root}\n"
            f"  config file:   {config_file}\n"
            f"  Fix: resolve_root.py set-root --root <new-abs-path>\n"
            f"       (常见原因：vault 被重命名 / 外置盘未挂载 / 路径大小写变了)\n"
        )
        return 4

    sys.stdout.write(f"✓ specode doctor: specsRoot ok — {specs_root}\n")
    if legacy and "specsRoot" in cfg:
        # Both keys present — legacy is stale baggage.
        sys.stdout.write(
            f"⚠ legacy `obsidianRoot` key still in {config_file}\n"
            f"  value: {legacy}\n"
            f"  Suggest re-run `set-root --root {specs_root}` to clean it up\n"
            f"  (other plugins that still read obsidianRoot may follow this\n"
            f"  stale path → split-brain risk).\n"
        )
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="resolve_root.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get-root")
    g.add_argument("--root")
    g.set_defaults(func=cmd_get_root)

    s = sub.add_parser("set-root")
    s.add_argument("--root", required=True)
    s.set_defaults(func=cmd_set_root)

    d = sub.add_parser("doctor")
    d.set_defaults(func=cmd_doctor)

    lp = sub.add_parser("list-specs")
    lp.add_argument("--root")
    lp.set_defaults(func=cmd_list_specs)

    rp = sub.add_parser("resolve-project-root")
    rp.add_argument("--cwd")
    rp.set_defaults(func=cmd_resolve_project_root)

    wp = sub.add_parser("write-project-root")
    wp.add_argument("--spec", required=True)
    wp.add_argument("--root", required=True)
    wp.set_defaults(func=cmd_write_project_root)

    rdp = sub.add_parser("read-project-root")
    rdp.add_argument("--spec", required=True)
    rdp.set_defaults(func=cmd_read_project_root)

    du = sub.add_parser("plan-unchecked", aliases=["design-unchecked"],
                        help="count unchecked '- [ ]' steps in the spec's plan "
                             "(tasks.md; 5.x legacy: design.md) "
                             "(0 ok / 2 has-unchecked / 3 no-plan)")
    du.add_argument("--spec", required=True)
    du.set_defaults(func=cmd_plan_unchecked)

    # v0.9 M1/M9 (3.4.0): autonomous-mode defaults
    rd = sub.add_parser("read-defaults",
                        help="read autonomous-mode defaults (env > file > schema)")
    rd.add_argument("--key", default=None,
                    help="key name; omit to dump all as JSON")
    rd.add_argument("--json", action="store_true",
                    help="emit JSON {value, source} even for single key")
    rd.set_defaults(func=cmd_read_defaults)

    wd = sub.add_parser("write-default",
                        help="persist a defaults key to ~/.config/specode/defaults.json")
    wd.add_argument("--key", required=True)
    wd.add_argument("--value", required=True)
    wd.set_defaults(func=cmd_write_default)

    xd = sub.add_parser("reset-default",
                        help="remove a defaults key (or --all to wipe)")
    xd.add_argument("--key", default=None)
    xd.add_argument("--all", action="store_true")
    xd.set_defaults(func=cmd_reset_default)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
