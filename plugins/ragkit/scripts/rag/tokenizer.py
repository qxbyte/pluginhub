"""Unified tokenization for docs AND queries — one regex family, no drift (V3 #2/#11 根治)."""
from __future__ import annotations

import re

_ASCII = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+")
_CJK_RUN = re.compile(r"[一-鿿]{2,}")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for word in _ASCII.findall(text):
        lw = word.lower()
        tokens.append(lw)
        parts = [p.lower() for p in _CAMEL.findall(word) if len(p) >= 2]
        if len(parts) > 1:
            tokens.extend(p for p in parts if p != lw)
    for run in _CJK_RUN.findall(text):
        tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


def extract_focus(query: str, threshold: int = 100) -> str:
    if len(query) < threshold:
        return query
    lines = [ln.strip() for ln in query.splitlines() if ln.strip()]
    head = lines[0] if lines else ""
    seen: set[str] = set()
    idents: list[str] = []
    for w in _ASCII.findall(query):
        if w.lower() not in seen:
            seen.add(w.lower())
            idents.append(w)
    return (head + " " + " ".join(idents[:30]))[:400]
