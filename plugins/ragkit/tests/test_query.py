import json

from rag import backend, store
from rag.chunker import chunk_kb
from rag.pipeline import query_pipeline


def _build_index(kb, with_vectors=True):
    chunks = chunk_kb(kb)
    if with_vectors:
        backend.save_config(kb, {"backend": "dummy"})
        vecs = backend.encode("dummy", {}, [c.text for c in chunks])
        store.save_index(kb, chunks, vecs, "dummy::dummy")
    else:
        store.save_index(kb, chunks, None, "")


def test_pipeline_full_three_channels(kb):
    _build_index(kb)
    out = query_pipeline(kb, "银行账号脱敏规则")
    assert out["vector_channel"] == "ok"
    assert out["results"][0]["knowledge_id"] == "114371-mask-rule"
    assert "vector" in out["results"][0]["ranked_by"]
    assert "lexical" in out["results"][0]["ranked_by"]


def test_pipeline_degrades_without_vectors(kb):
    _build_index(kb, with_vectors=False)
    out = query_pipeline(kb, "见费出单收款页面在哪")
    assert out["vector_channel"] == "no_backend"
    assert out["results"][0]["knowledge_id"] == "cod-receipt-page"


def test_pipeline_no_index(kb):
    out = query_pipeline(kb, "任意问题")
    assert out["vector_channel"] == "no_index"
    assert out["results"] == []


def test_pipeline_degrades_on_vector_backend_error(kb, monkeypatch):
    """云端认证失败/网络抖动时不整体崩溃，降级到词汇+元数据路。"""
    _build_index(kb)  # 索引带 dummy 向量，backend 解析仍为 dummy

    def _boom(*a, **k):
        raise urllib_error()

    monkeypatch.setattr(backend, "encode", _boom)
    out = query_pipeline(kb, "银行账号脱敏规则")
    assert out["vector_channel"] == "vector_error"
    assert "vector_error_detail" in out
    # 关键：词汇/元数据路仍返回结果，query 不崩
    assert out["results"][0]["knowledge_id"] == "114371-mask-rule"
    assert "vector" not in out["results"][0]["ranked_by"]


def urllib_error():
    import urllib.error
    return urllib.error.HTTPError("http://x/embeddings", 401, "Unauthorized", {}, None)


def test_cli_query_json(kb, run_cli):
    _build_index(kb)
    res = run_cli("query", "银行账号脱敏", "--kb", str(kb), "--json")
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["results"][0]["knowledge_id"] == "114371-mask-rule"


def test_cli_query_markdown_card(kb, run_cli):
    _build_index(kb)
    res = run_cli("query", "银行账号脱敏", "--kb", str(kb))
    assert res.returncode == 0
    assert "RagKit 召回" in res.stdout
    assert "cases/114371-mask-rule.md" in res.stdout
    assert "非事实来源" in res.stdout


def test_cli_query_unknown_channel_returns_2(kb, run_cli):
    res = run_cli("query", "x", "--kb", str(kb), "--channels", "lexcial")
    assert res.returncode == 2
