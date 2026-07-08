---
name: status
description: Use when checking RagKit index health — doc and chunk counts, backend resolution, staleness and drift between knowledge-base/ and index. Trigger /ragkit:status. Rebuilding after drift uses ragkit:embed.
---

# RagKit Status

脚本在本插件的 `scripts/` 目录（本 skill 目录的上两级）；用本 skill 的 base directory 把下面的相对路径拼成绝对路径执行。

```sh
sh ../../scripts/run.sh ../../scripts/ragkit.py \
   status --kb <项目根>/knowledge-base --json
```

解读：`drift.missing_from_index` 非空或 `index_stale: true` → 建议重跑 embed；`backend_resolved: none` → 原样转述固定提示块。
