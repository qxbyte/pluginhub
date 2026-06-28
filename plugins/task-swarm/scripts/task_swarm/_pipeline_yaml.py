"""pipeline.yml YAML-subset parser — stdlib-only, pure function.

Supports a deliberately restricted YAML subset (block maps with 2-space
indent, block lists, flow lists, single-line scalars, single/double quoted
strings, full-line + inline comments). Anything outside the subset raises
``PipelineYamlError`` with a line number and the offending construct name —
the parser never silently mis-parses.

The strict subset is a **design feature**, not a limitation worth fixing
with PyYAML: pipeline.yml is configuration not arbitrary YAML, and the
parser's per-construct line-number errors are higher signal than PyYAML's
silent yes/no→bool / 1.0→float quirks. v0.9 试跑 M11（"YAML subset 不支持
anchor/flow map"）评估结论：**不引入 PyYAML**——这违反"never silently
mis-parse"的核心契约。如需更复杂 YAML feature，重写 pipeline.yml 为 subset
即可。
"""
from __future__ import annotations

import re


class PipelineYamlError(Exception):
    pass


def _err(lineno, msg, line):
    return PipelineYamlError(f"line {lineno}: {msg}: {line.rstrip()!r}")


def _strip_comment(line):
    """Cut the line at the first unquoted ``#``.

    Tracks single/double quote state so a ``#`` inside a quoted string stays
    literal. Leading spaces are preserved so the caller can still compute
    indentation. A ``#`` is only a comment opener when it is the first char or
    preceded by whitespace (mirrors YAML), so ``a#b`` stays intact.
    """
    out = []
    in_single = in_double = False
    prev = ""
    for ch in line:
        if ch == "#" and not in_single and not in_double and (prev == "" or prev == " "):
            break
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _parse_quoted(s, lineno):
    q = s[0]
    if len(s) < 2 or s[-1] != q:
        raise PipelineYamlError(f"line {lineno}: unterminated quoted string: {s!r}")
    body = s[1:-1]
    if q == "'":
        return body
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _split_flow(s):
    """Split a flow-list body on top-level commas (quote-aware)."""
    parts = []
    cur = []
    in_single = in_double = False
    for ch in s:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == "," and not in_single and not in_double:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip() != "" or parts:
        parts.append("".join(cur))
    return parts


def _parse_flow_list(s, lineno, line):
    inner = s[1:-1].strip()
    if inner == "":
        return []
    items = []
    for part in _split_flow(inner):
        elem = part.strip()
        if elem and elem[0] in ("[", "{"):
            raise _err(lineno, "nested flow not supported", line)
        items.append(_value(part, lineno, line))
    return items


def _value(raw, lineno, line):
    """Parse a single value token (scalar / quoted / flow list)."""
    s = raw.strip()
    if s == "":
        return None
    if s[0] in ("|", ">"):
        raise _err(lineno, "block scalar not supported", line)
    if s[0] == "{":
        raise _err(lineno, "flow map not supported", line)
    if s.startswith("!!") or s[0] == "!":
        raise _err(lineno, "tag not supported", line)
    if s[0] == "&":
        raise _err(lineno, "anchor not supported", line)
    if s[0] == "*":
        raise _err(lineno, "alias not supported", line)
    if s[0] in ("'", '"'):
        return _parse_quoted(s, lineno)
    if s[0] == "[":
        if not s.endswith("]"):
            raise PipelineYamlError(f"line {lineno}: malformed flow list: {s!r}")
        return _parse_flow_list(s, lineno, line)
    return _scalar(s, lineno)


def _scalar(raw, lineno):
    s = raw.strip()
    if s in ("", "null", "~"):
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _is_map_entry(content):
    """True if ``content`` is a ``key: value`` entry (quote-aware colon scan)."""
    in_single = in_double = False
    for i, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            # "key:" at end or "key: value"
            if i + 1 == len(content) or content[i + 1] == " ":
                return True
    return False


def _split_kv(content):
    """Split a map entry into (key, value) at the first unquoted ``: ``/``:``."""
    in_single = in_double = False
    for i, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            if i + 1 == len(content) or content[i + 1] == " ":
                return content[:i].strip(), content[i + 1:].strip()
    return content.strip(), ""


def parse(text):
    lines = text.splitlines()
    rows = []
    for i, line in enumerate(lines, 1):
        line = _strip_comment(line)
        if line.strip() == "":
            continue
        if line.strip() in ("---", "...") or line.startswith("--- ") or line.startswith("... "):
            raise _err(i, "multi-document not supported", line)
        indent = len(line) - len(line.lstrip(" "))
        if "\t" in line[:indent + 1]:
            raise _err(i, "tab indentation not allowed", line)
        if indent % 2 != 0:
            raise _err(i, "indentation must be a multiple of 2 spaces", line)
        rows.append((i, indent, line.strip(), line))

    def build(rows, base_indent):
        if rows and rows[0][2].startswith("- ") or rows and rows[0][2] == "-":
            return build_list(rows, base_indent)
        return build_map(rows, base_indent)

    def build_map(rows, base_indent):
        result = {}
        idx = 0
        while idx < len(rows):
            lineno, indent, content, raw = rows[idx]
            if indent < base_indent:
                break
            key, val = _split_kv(content)
            if key == "<<":
                raise _err(lineno, "merge key (alias) not supported", raw)
            if val == "":
                sub = []
                j = idx + 1
                while j < len(rows) and rows[j][1] > indent:
                    sub.append(rows[j])
                    j += 1
                result[key] = build(sub, indent + 2) if sub else None
                idx = j
            else:
                result[key] = _value(val, lineno, raw)
                idx += 1
        return result

    def build_list(rows, base_indent):
        result = []
        idx = 0
        while idx < len(rows):
            lineno, indent, content, raw = rows[idx]
            if indent < base_indent:
                break
            # content begins with "- " (or bare "-"); everything after is the
            # first virtual row of this item, sitting at indent + 2.
            rest = content[1:].lstrip(" ") if content == "-" else content[2:]
            item_indent = indent + 2
            item_rows = []
            if rest != "":
                item_rows.append((lineno, item_indent, rest, raw))
            j = idx + 1
            while j < len(rows) and rows[j][1] > indent:
                item_rows.append(rows[j])
                j += 1
            if not item_rows:
                result.append(None)
            elif len(item_rows) == 1 and not _is_map_entry(item_rows[0][2]):
                result.append(_value(item_rows[0][2], item_rows[0][0], item_rows[0][3]))
            else:
                result.append(build(item_rows, item_indent))
            idx = j
        return result

    return build(rows, 0)
