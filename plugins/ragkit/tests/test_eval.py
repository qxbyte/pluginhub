import json
from pathlib import Path

import pytest

from rag import backend, store
from rag.chunker import chunk_kb
from rag.evaluate import run_evalset


@pytest.fixture
def eval_kb(tmp_path, monkeypatch):
    """Extended knowledge base with more docs to prevent accidental matches on unrelated queries."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    monkeypatch.delenv("HF_ENDPOINT", raising=False)
    root = tmp_path / "knowledge-base"
    (root / "cases").mkdir(parents=True)
    (root / "navigation").mkdir()

    # Primary test docs
    mask_doc = """---
标题: 银行账号脱敏规则（前六后四）
类型: case
来源: 114371-收付个人数据脱敏需求
tags: [银行账号脱敏, 前六后四, DesensitizeUtils]
描述: 银行账号展示脱敏：保留前六后四，工具类 DesensitizeUtils.mask()。
---

## 定位

- 工具方法 `DesensitizeUtils.mask(String bankAccount)`，长度 <=10 透传。

## 可复用经验 / 坑

- 编辑场景不脱敏，前端保留隐藏真实账号字段。
"""

    auth_doc = """---
标题: authorityQueryByPaymentNo 三步查询链路
类型: case
来源: 121659-非见费出单收付登记号授权功能
tags: [SfPlanAuthorityBizImpl, paymentNo, SfPaymentMain]
描述: authorityQuery 按 paymentNo 查询的三步链路。
---

## 定位

- SfPlanAuthorityBizImpl.authorityQueryByPaymentNo → SfPaymentMain 校验 → SfPolicyPayment。
"""

    nav_doc = """---
标题: 见费出单收款页面前后端定位
类型: navigation
来源: 125577-生成流水号时修改收付机构功能关闭
tags: [SfCodDeal, 见费出单, 见费收款]
描述: 见费出单收款页面与提交接口定位
---

# 见费出单收款页面前后端定位

## 答案路径

- 页面：`SfCodDeal.vue`；新收款：`SfBusinessCredit.credit`。
"""

    # Filler docs to prevent accidental matches
    filler_docs = [
        ("cases", "000-python-basics", """---
标题: Python基础知识
类型: case
---
Python是一种编程语言，支持多种编程范式。学习Python需要理解函数、类、模块等概念。
"""),
        ("cases", "001-database-design", """---
标题: 数据库设计原则
类型: case
---
关系数据库遵循范式化设计，包括第一范式、第二范式、第三范式等概念。
"""),
        ("cases", "002-rest-api", """---
标题: RESTful API设计
类型: case
---
RESTful API使用HTTP方法如GET、POST、PUT、DELETE进行操作，遵循无状态设计原则。
"""),
        ("navigation", "003-linux-commands", """---
标题: Linux常用命令
类型: navigation
---
Linux系统中常用的命令包括ls、cd、mkdir、rm等文件操作命令。
"""),
        ("navigation", "004-git-workflow", """---
标题: Git工作流程
类型: navigation
---
Git是分布式版本控制系统，支持分支管理、提交、合并等操作。
"""),
    ]

    (root / "cases" / "114371-mask-rule.md").write_text(mask_doc, encoding="utf-8")
    (root / "cases" / "121659-authority-chain.md").write_text(auth_doc, encoding="utf-8")
    (root / "navigation" / "cod-receipt-page.md").write_text(nav_doc, encoding="utf-8")

    for cat, name, content in filler_docs:
        (root / cat / f"{name}.md").write_text(content, encoding="utf-8")

    return root


def _index(kb):
    chunks = chunk_kb(kb)
    backend.save_config(kb, {"backend": "none"})  # No vector embeddings, only lexical+metadata
    store.save_index(kb, chunks, None, "")


def test_run_evalset_metrics(eval_kb):
    _index(eval_kb)
    evalset = [
        {"query": "银行账号脱敏规则", "expect": ["114371-mask-rule"], "bucket": "case"},
        {"query": "见费出单收款页面在哪", "expect": ["cod-receipt-page"], "bucket": "navigation"},
        {"query": "完全无关的火星话题", "expect": ["114371-mask-rule"], "bucket": "case"},
    ]
    report = run_evalset(eval_kb, evalset, top=5)
    assert report["n"] == 3
    assert 0 < report["recall_at_top"] < 1        # 两中一漏
    assert report["mrr"] > 0
    assert set(report["by_bucket"]) == {"case", "navigation"}
    assert report["misses"][0]["query"] == "完全无关的火星话题"


def test_eval_cli_with_channel_filter(kb, run_cli, tmp_path):
    _index(kb)
    es = tmp_path / "es.json"
    es.write_text(json.dumps([
        {"query": "银行账号脱敏", "expect": ["114371-mask-rule"], "bucket": "case"},
    ], ensure_ascii=False), encoding="utf-8")
    res = run_cli("eval", "--kb", str(kb), "--evalset", str(es),
                  "--channels", "lexical,metadata", "--json")
    assert res.returncode == 0, res.stderr
    report = json.loads(res.stdout)
    assert report["recall_at_top"] == 1.0


def test_bundled_evalset_is_valid_json():
    from pathlib import Path

    import rag

    data = json.loads((Path(rag.__file__).parent / "evalset.json").read_text(encoding="utf-8"))
    assert len(data) >= 15
    assert all({"query", "expect", "bucket"} <= set(item) for item in data)
