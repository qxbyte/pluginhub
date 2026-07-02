"""Golden-set evaluation: recall@top + MRR, bucketed by knowledge type."""
from __future__ import annotations

from pathlib import Path

from .pipeline import query_pipeline


def run_evalset(kb_root: Path, evalset: list[dict], top: int = 5,
                channels_filter: list[str] | None = None) -> dict:
    rows = []
    for item in evalset:
        out = query_pipeline(kb_root, item["query"], top=top, channels_filter=channels_filter)
        got = [r["knowledge_id"] for r in out["results"]]
        rank = next((i + 1 for i, kid in enumerate(got) if kid in set(item["expect"])), 0)
        rows.append({"query": item["query"], "expect": item["expect"],
                     "bucket": item.get("bucket", "?"), "got": got, "rank": rank})

    def _metrics(subset: list[dict]) -> dict:
        n = len(subset)
        hits = sum(1 for r in subset if r["rank"])
        mrr = sum(1.0 / r["rank"] for r in subset if r["rank"]) / n if n else 0.0
        return {"n": n, "recall_at_top": round(hits / n, 4) if n else 0.0, "mrr": round(mrr, 4)}

    report = _metrics(rows)
    report["by_bucket"] = {
        b: _metrics([r for r in rows if r["bucket"] == b])
        for b in sorted({r["bucket"] for r in rows})
    }
    report["misses"] = [{"query": r["query"], "expect": r["expect"], "got": r["got"]}
                        for r in rows if not r["rank"]]
    return report
