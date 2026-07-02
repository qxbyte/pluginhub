"""Reciprocal Rank Fusion across recall channels."""
from __future__ import annotations

RRF_K = 60

# 通道权重（2026-07-03 优化轮 E2c，真实语料双评测集选定）：
# 定位型知识库里精确措辞证据（标识符/页面名/字段名）比语义联想更可信，
# lexical 1.2 是唯一让全通道在标准集与语义压力集上都 ≥ 纯词汇基线的配置
# （标准 mrr 0.7937→0.8250，压力 mrr 0.6111 仍 ≥ 基线 0.5889）。
CHANNEL_WEIGHTS = {"lexical": 1.2, "metadata": 1.0, "vector": 1.0}


def rrf_fuse(rankings: dict[str, list[str]], k: int = RRF_K,
             weights: dict[str, float] | None = None) -> list[dict]:
    w = CHANNEL_WEIGHTS if weights is None else weights
    scores: dict[str, float] = {}
    ranked_by: dict[str, list[str]] = {}
    for channel in sorted(rankings):
        cw = w.get(channel, 1.0)
        for rank, kid in enumerate(rankings[channel]):
            scores[kid] = scores.get(kid, 0.0) + cw / (k + rank + 1)
            ranked_by.setdefault(kid, []).append(channel)
    fused = [
        {"knowledge_id": kid, "rrf_score": round(s, 6), "ranked_by": ranked_by[kid]}
        for kid, s in scores.items()
    ]
    fused.sort(key=lambda x: (-x["rrf_score"], x["knowledge_id"]))
    return fused
