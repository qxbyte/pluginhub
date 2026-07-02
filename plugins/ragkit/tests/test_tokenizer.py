from rag.tokenizer import extract_focus, tokenize


def test_tokenize_chinese_bigrams_and_ascii():
    toks = tokenize("工单指派 IT 成员")
    assert "工单" in toks and "单指" in toks and "指派" in toks
    assert "it" in toks  # 2-letter acronym must survive (V3 痛点 #2)


def test_tokenize_camel_case_split():
    toks = tokenize("SfPlanAuthorityBizImpl")
    assert "sfplanauthoritybizimpl" in toks
    assert "plan" in toks and "authority" in toks


def test_short_query_passthrough():
    q = "银行账号脱敏"
    assert extract_focus(q) == q


def test_long_query_extracts_head_and_identifiers():
    q = "需求标题：授权功能调整\n" + "背景说明" * 60 + "\n涉及 SfPlanAuthority 与 paymentNo 字段"
    focus = extract_focus(q)
    assert len(focus) < len(q)
    assert "授权功能调整" in focus
    assert "SfPlanAuthority" in focus and "paymentNo" in focus
