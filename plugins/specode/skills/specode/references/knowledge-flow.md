---
description: One-page mental model of specode's experience/knowledge loop — who produces, who indexes, who reads, and when. Read this to understand how distill / knowledge-base / MEMORY / ragkit / intake-retrieval fit together.
---

# 知识流心智模型（谁产 · 谁索引 · 谁读 · 何时）

一句话：**KB 是「定位用，非事实用」。** 它只提供指针（文件路径 + 调用链 + 导航经验）帮你更快跳到真实代码；**真实代码始终是唯一事实来源**。绝不允许仅凭 KB 内容推进新需求。

```
  产出（写）                        索引                      消费（读）
  ─────────────────────────         ───────────────           ─────────────────────────────
  /specode:distill <slug>           MEMORY.md                 intake（requirements 项目分析）
   （手动，验收末尾按                （小 md 索引，列           = 主检索节点
    auto_distill 提示；               标题/类型/描述/           · Tier-1 读 MEMORY 比对页面/字段/域
    绝不自动跑）                      来源/路径/tags）          · 命中 → Tier-2 读 ≤5 点 → 跳真实代码
        │                                ▲                     · 若装 ragkit 且 chunks.json 存在
        ▼                                │ memory-rebuild        → Tier-0 ragkit:query 多路召回
  <project_root>/knowledge-base/    （由各文档 frontmatter          │
   ├── cases/<topic>.md    ────────► 全量重建，不手改）              ▼
   ├── navigation/<topic>.md         .ragkit/（可选）          design（条件性 top-up）
   └── MEMORY.md                     chunks.json + vectors     = 默认继承 intake 指针，
        │                            由 /ragkit:embed 建         仅新领域才补查
        │（可选副本）                 （仅装 ragkit 时）              │
        ▼                                                          ▼
   Obsidian vault                                            把设计/需求 ground 到真实代码
   （knowledge.py copy-to，                                   （tasks / 执行 / task-swarm = 零注入）
    人读镜像）
```

## 铁律

- **产出是手动的**：只有 `/specode:distill <slug>` 写 KB；主流程绝不自动沉淀（验收末尾只*提示*入口，按 `auto_distill` 决定）。
- **frontmatter 是单一事实源**：`MEMORY.md` 永远由 `knowledge.py memory-rebuild` 从各文档 frontmatter 全量重建，**不手改**（`memory-validate` 查漂移）。
- **消费只在两处**：intake 的项目分析步（主节点）+ design（条件性 top-up）。**tasks / 执行 / task-swarm 零注入**——到那时文件路径已在 design.md / tasks.md 里。
- **注入是指针非事实**：贴成「参考定位（非事实来源）」段，只用于定位、不写进 requirements.md 的事实结论。
- **全程 opt-in**：无 `knowledge-base/MEMORY.md` → 检索静默跳过（默认成本 ≈ 一次小索引读）。无 ragkit → Tier-0 不生效，退到 Tier-1/2。
- **`knowledge-base/` 不入仓**：本地私有定位资产（`ensure-gitignore` 保证）；Obsidian 副本是可选的人读镜像。

## 契约锁步 🔒

MEMORY 列 + frontmatter 键在三处必须一致：`skills/distill/references/doc-template.md`（写）、`scripts/knowledge.py` `_COLS`（索引）、`skills/specode/references/retrieval.md`（读）。改一处 → 改三处。`tests/test_contract_lockstep.py` 是这条纪律的 CI 门禁。

## 各部件的权威文档

- 产出：`skills/distill/SKILL.md` + `skills/distill/references/doc-template.md`
- 索引 CLI：`scripts/knowledge.py`（`memory-rebuild` / `memory-validate` / `copy-to` / `ensure-gitignore`）
- 消费：`skills/specode/references/retrieval.md`（Tier-0 gate + 两级 gated）
- 主消费方：`skills/intake/SKILL.md` §Step 2b
