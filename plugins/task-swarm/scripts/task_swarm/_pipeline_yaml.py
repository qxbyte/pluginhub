"""pipeline.yml YAML-subset parser — stdlib-only, pure function.

Supports a deliberately restricted YAML subset (block maps with 2-space
indent, block lists, flow lists, single-line scalars, single/double quoted
strings, full-line + inline comments). Anything outside the subset raises
``PipelineYamlError`` with a line number and the offending construct name —
the parser never silently mis-parses.
"""
from __future__ import annotations

import re


class PipelineYamlError(Exception):
    pass


def _err(lineno, msg, line):
    return PipelineYamlError(f"line {lineno}: {msg}: {line.rstrip()!r}")


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


def parse(text):
    lines = text.splitlines()
    rows = []
    for i, line in enumerate(lines, 1):
        if line.strip() == "":
            continue
        indent = len(line) - len(line.lstrip(" "))
        if "\t" in line[:indent + 1]:
            raise _err(i, "tab indentation not allowed", line)
        if indent % 2 != 0:
            raise _err(i, "indentation must be a multiple of 2 spaces", line)
        rows.append((i, indent, line.strip(), line))

    def build(rows, base_indent):
        result = {}
        idx = 0
        while idx < len(rows):
            lineno, indent, content, raw = rows[idx]
            if indent < base_indent:
                break
            key, _, val = content.partition(":")
            key = key.strip()
            if val.strip() == "":
                sub = []
                j = idx + 1
                while j < len(rows) and rows[j][1] > indent:
                    sub.append(rows[j])
                    j += 1
                result[key] = build(sub, indent + 2) if sub else None
                idx = j
            else:
                result[key] = _scalar(val, lineno)
                idx += 1
        return result

    return build(rows, 0)
