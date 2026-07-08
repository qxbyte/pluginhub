---
name: eval
description: Use when measuring or tuning RagKit retrieval accuracy — runs the golden evalset, reports recall@k and MRR per bucket. Trigger /ragkit:eval. Run before or after any retrieval-param change to keep a baseline.
---

# RagKit Eval

脚本在本插件的 `scripts/` 目录（本 skill 目录的上两级）；用本 skill 的 base directory 把下面的相对路径拼成绝对路径执行。

```sh
sh ../../scripts/run.sh ../../scripts/ragkit.py \
   eval --kb <知识库路径> [--evalset <file>] [--channels lexical,metadata]
```

- `--channels lexical,metadata` = 无向量基线；与全通道对比即向量路增益。
- 任何检索参数调优（分词/权重/RRF）都必须先跑 eval 留对照数字。
