---
name: using-ragkit
description: Overview of the ragkit plugin and how to use it — knowledge-base multi-channel retrieval and its four skills. On Kimi Code this is loaded at session start via the manifest's sessionStart.skill; on hosts with a SessionStart hook the same advisory is injected by the hook instead.
---

# using-ragkit — ragkit 可用性说明（会话启动注入）

> 本技能是 ragkit 的**会话启动 advisory**。在 Kimi Code 由清单的 `sessionStart.skill` 于会话开始时注入；在有 SessionStart hook 的宿主（Claude Code / CodeBuddy）由 hook 注入等价文案，无需本技能。

RagKit 可用：对项目 `knowledge-base/` 做多路检索（向量 + 词汇 + 元数据，RRF 融合）。四个技能：

- `ragkit:query` — 检索，返回定位卡片（非事实来源，仅用于快速定位真实代码）。
- `ragkit:embed` — 构建 / 更新向量索引。
- `ragkit:status` — 索引健康 / drift。
- `ragkit:eval` — 检索精度评估。

用户要检索 / 建索引 / 查健康时，用 `Skill` 工具（或宿主等价的 skill 调用机制）**按名调用**对应技能（`/ragkit:*` 或直接按名，无需去找命令文件）。

硬约束（防脱轨）：① 只按名调技能，**绝不在文件系统里搜 skill / 脚本文件**——插件文件在插件缓存目录、不在你的项目里，技能内部会自己定位脚本；② 检索**只能**调 RagKit 的脚本，**严禁**自己读 `.ragkit` 向量文件、装 numpy、或用 embedding API 手搓相似度（结果会错且不可复现）；③ 脚本定位 / 运行失败 → 停下报确切错误，不要绕过、不要自己实现。
