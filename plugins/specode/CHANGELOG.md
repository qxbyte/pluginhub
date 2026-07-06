# Changelog — specode

specode 是 spec-driven 轻量工作流插件：requirements → design → tasks → execute → acceptance 五阶段编排 + 四份固定产物（requirements.md / design.md / tasks.md / implementation-log.md）。本文件记录其自身版本。

## Unreleased

## 6.1.5 (2026-07-06) — skill description 统一模板

- **skill `description` 统一为渐进式加载模板（零行为变化）**：三个 skill（specode / intake / distill）的 frontmatter `description` 是 agent 渐进式加载时**唯一常驻**的元数据，模型据此决定何时唤起该 skill。统一改写为「用途场景开头（Use when …）→ 做什么/产物 → Trigger 触发词/命令 → 边界/谁触发」的轻量模板，并删去描述里的版本史噪音（如 intake 的「replaces the old brainstorming…」）。正文与行为逻辑一字未动。

## 6.1.4 (2026-07-05)

- **marketplace 加 `category` 字段**：在 `.claude-plugin/marketplace.json` 的 specode 条目加 `"category": "development"`，让 `/plugin` Discover 面板在插件名后显示 `[development]` 标签（对齐官方市场；该字段只在 marketplace.json、UI 只读它）。零行为变化。

## 6.1.3 (2026-07-05)

- **`description` 字段收敛为「当前插件说明」，不再堆版本史**：marketplace UI 显示的是 `.claude-plugin/marketplace.json` + `plugin.json` 的 `description` 字段，此前每次 release 把 `**vX.Y.Z**: …` 往前追加、从不删旧的，累积到 2601 字符（9+ 版全在里面）。现清成一句话讲插件当前干嘛（intake / task-swarm 衔接 / 可选检索），版本历史只留在 CHANGELOG。README 表格行 + 徽章同步。**go-forward 规则**：release 只 bump 版本 + 写 CHANGELOG，`description` 仅在插件用途本身变化时才动，永不再堆版本 blurb。

## 6.1.2 (2026-07-05)

- **插件语言统一（仅 specode，零行为变化）**：把面向 agent 的**指令 / 说明性 prose 全部转成地道英文**（按中文语义转写，非直译）——`skills/*/SKILL.md`（specode / intake / distill）、`skills/specode/references/*.md`（retrieval / obsidian / superpowers-wiring / knowledge-flow）、`commands/*.md`、以及三个脚本的 docstring + 行内注释。
- **用户可见的固定输出与选择保持中文**（明确不动）：执行方式 selector 的选项文案（`references/selectors.md` 未动）、`assets/templates/*.md`（生成的 spec 文档模板）、注入用户文档的段（`## 项目级约束` / `## 参考定位（非事实来源）`）、脚本 stderr/stdout 用户消息、SessionStart DISCIPLINE 提示、MEMORY.md 输出说明、以及 `_COLS` / frontmatter 键标识符（`标题/类型/描述/来源/路径/tags`）。
- **CHANGELOG 永远保持中文**（本次及以后）。测试零回归（90 passed），契约锁步门禁验证 MEMORY 列未受影响。

- **契约锁步 CI 门禁**（`tests/test_contract_lockstep.py`）：把 CLAUDE.md 的「变更纪律」变成可执行测试——读 `knowledge.py` **真实**产出的 MEMORY 表头（跑 memory-rebuild，非源码内省），断言它与 `references/retrieval.md`、`skills/distill/references/doc-template.md` 文档化的列一致，并断言 doc-template 的 frontmatter 键 == knowledge.py 读的键。提取器经**负控验证**能抓 reorder/drop，门禁可真失败而非白过。三处任一漂移 → 测试红。（+5 测，共 90。）
- **一页纸知识流心智模型**（`references/knowledge-flow.md`）：ASCII 产出→索引→消费全图（distill 写 / `knowledge.py` 索引 / intake+design 读、tasks+执行零注入）+ 「定位用非事实用」不变量 + 各部件权威文档指针。挂进 SKILL/intake References + 两 README 架构树（顺带把 `autonomous-mode.md` 补进树）。

- **新增独立 intake skill**（`skills/intake/`，与 `distill` 平级，`user-invocable: false`，由编排 SKILL 经 Skill 工具按名 `specode:intake` 调用）接管 **requirements phase**：项目分析（agent-docs 扫描 + 经验检索 + 读定位到的真实代码）→ 基于分析的澄清（brainstorming 级，非固定问卷）→ 写 `requirements.md`。**保留 frontmatter 契约不动**：`spec_id` / `created_at` / `project_root`（后者仍经 `write-project-root` 单一写入口）。
- **修正 6.0.0 的 brainstorming 双产物错位**：brainstorming 从此**只产 design.md（单产物）**，requirements 由 intake 产。requirements phase 不再分「superpowers 在/不在」——永远走 intake，消掉一个 fork。relocate 后置检查回到单文件。
- **检索节点收敛**：主节点移到 intake 的项目分析步；**design 降为条件性 top-up**（默认继承 intake 指针，仅新领域才补查）；tasks / 执行零注入不变。
- **弊端修复**：writing-plans 结尾硬编码的「Subagent vs Inline」执行方式提问无参数可关——SKILL 措辞从「抑制」改为**「忽略、不据此执行，继续走 specode selector」**（诚实：只能消化不能抑制）。
- **SKILL 轻量化（零行为变化）**：`skills/specode/SKILL.md` 215 → 171 行——完整 `resolve_root.py` verb 表下沉到 `references/obsidian.md`；autonomous-mode mapping + 决策伪代码抽到新 `references/autonomous-mode.md`；resolver why-prose 精简；v4.0.0 移除说明压成一行；重复三处的 Absence-fallback 矩阵 slim 成指针。
- **清理 v3/codemap 死术语噪声（零行为变化）**：功能层无残留（codemap / `.ai-memory` 活代码路径在 4.0.0/5.0.1 已干净移除）；但 `distill` skill 反复对着已不存在的工具声明「无 codemap knowledge write / 不调 codemap recall / 不读 .ai-memory」约 5 处——收敛为中性的活约束（md-only / 不消费旧 KB 当事实 / 不喂下游），历史细节留 CHANGELOG，仅保留一条 checkout-backup 逃生指针。

- **BREAKING**: 固定产物 3 → 4 —— `design.md` 重定义为**传统设计文档**（背景与目标/架构概览/模块划分/接口设计/数据流/错误处理/测试策略，散文无 checkbox）；新增 `tasks.md` 承载可执行计划（writing-plans 格式 + `**Interfaces:**` 契约块，引擎中立，task-swarm / superpowers / 自执行统一消费）。流水线变为 requirements → design → tasks → 执行方式 selector → 执行 → 验收；brainstorming 一次跨 requirements+design 双产物落盘（后置 relocate 检查两份）。
- **BREAKING**: continue 改「加载即停」——`/specode:continue <slug>` 只读文档 + 汇报进度简报（阶段/文档状态/checkbox x/N）后停下等用户指令，不再自动续跑；用户说「继续」才从推断阶段续跑，提出需求变更则先消化进文档再问。
- `resolve_root.py`：`_FIXED_DOCS` 加 `tasks.md`（list-specs 判定）；`design-unchecked` 更名 `plan-unchecked`（tasks.md 优先，design.md 含 checkbox 时按 5.x legacy 兜底；旧名保留为 alias）。distill 完成度检查与读文档集同步。
- 兼容：5.x 存量 spec（design.md 即计划）由 continue 推断表 legacy 行 + `plan-unchecked` 兜底识别，不中断。

## 5.2.0 (2026-07-03)

### Changed / Fixed
- retrieval.md Tier-0 RagKit gate 探针从 `test -d .ragkit` 收紧为
  `test -f .ragkit/chunks.json`，消除 `backend set` 只写 config.json
  时的假阳性（索引尚未构建即触发 gate）。
- Tier-0 采纳条目封顶 Tier-2 同等纪律：默认 ≤5 点/phase，复杂需求可标注理由突破。

### Added
- retrieval.md 新增 Tier-0 RagKit gate：检测到 ragkit 插件 + 已建索引时，
  requirements/design 的经验检索改走 `ragkit:query` 多路召回（模型自主提炼检索词、
  可多轮多角度）；未安装/未建索引零成本跳过，原两级 gated 流程不变。零依赖（zero-import）。

## 5.1.3 (2026-07-02) — list-specs intake 可见 + 文档陈旧内容清理

### Changed / Fixed

- **`list-specs` intake 阶段 spec 可见**（+3 测试）：原先只列含 `requirements.md` 的子目录，intake 阶段（目录已 `mkdir`、requirements 未写）的 spec 在 `/specode:list` 里隐身，与续接表里明确存在的 intake 状态不一致。现在列出「含任一固定产物（requirements / design / implementation-log.md）的子目录 + 空子目录（intake）」；隐藏目录（`.obsidian` 等）与只装无关内容的目录仍排除。
- **文档陈旧内容清理**：SKILL.md §Activation Guard 残留的 "in obsidian" 措辞改为 `<specsRoot>/<slug>/`（specsRoot 早已泛化，不再绑定 Obsidian）。

## 5.1.2 (2026-06-30) — distill 打磨（gitignore 非 git 跳过 / copy-to / nav 来源单值）

承接 5.1.1，第二轮真实项目试跑后的打磨项。

### Added

- **`knowledge.py copy-to --kb <src> --dest <abs>`**（+3 测试）：一步 dual-landing —— 把 `cases/` + `navigation/` 复制到绝对路径 dest 并重建该目录的 `MEMORY.md`（直写不拼接）。取代「手动 `cp` 两次 + 记得再 `memory-rebuild`」的多步法。

### Changed / Fixed

- **`ensure-gitignore` 非 git 跳过（F3）**：项目无 `.git` 且无既有 `.gitignore` 时跳过，不再创建无用的 stray `.gitignore`。
- **distill Step 5 改用 `copy-to`（F4）**：Obsidian 可选副本一步完成，杜绝漏跑 MEMORY 重建。
- **navigation `来源` 单值（F8）**：合并多 spec 的 navigation 点时 `来源` 保留首次引入的 slug，后续复用 spec 在正文列出（零 schema 影响）；并强化「写 navigation 前先 `Read` MEMORY 去重」。

### Notes

- **F5**（monorepo 项目级约束扫描）经评估不归 specode 管——用户在需要的项目目录自行放 `CLAUDE.md`/`CODEBUDDY.md`，扫描已认 `CODEBUDDY.md`。**F6**（prose 易漏步）由 F4 的 CLI 化顺带收敛。

## 5.1.1 (2026-06-30) — 试跑验证修复（distill 时机 / nav 去重 / 检索相关性）

承接 5.1.0，用真实项目（ops）多轮试跑验证后修三处。

### Added

- **`resolve_root.py design-unchecked --spec <dir>`**（+3 hermetic 测试）：数 `design.md` 里未勾选的 `- [ ]` Task —— exit 0=已执行完 / 2=有未勾选 / 3=无 design.md。distill 用它在沉淀前判断 spec 是否执行完。

### Changed / Fixed

- **distill 防悬空指针（F1）**：沉淀前跑 `design-unchecked`，spec 未执行完则 `AskUserQuestion` 告警（知识点可能引用未落地代码）；SKILL / `commands/distill.md` / `breakdown-heuristics.md` 补「执行 + 验收后再 distill」时机指引；`retrieval.md` 免责句补「指针可能指向计划中 / 已重构代码」。
- **distill navigation 去重（F7）**：写 navigation 点**前先 `Read` MEMORY** 按 tags+标题 比对，命中则合并而非新建（`memory-rebuild` 索引层不去重）；NO-recall 不变量补「读 MEMORY 仅用于去重比对」例外说明。
- **retrieval 相关性（F9）**：Tier-1 强调 `tags`/`描述` 命中只是候选，需判断改动类型 / 语义是否真适用，不适用不注入（避免退化成 v3 噪声注入）。

### Notes

- **F2（非 git / monorepo 的 project_root）评估为 by design 不修**：specode 不依赖 git，`project_root` 以 requirements.md frontmatter 里用户确认过的值为准，git-toplevel 只是默认建议值。

## 5.1.0 (2026-06-30) — 重新引入经验检索注入（定位用·非事实用）

把 v4.0.0 拔掉的「检索注入」以全新路线重新引入：KB 是**定位用、非事实用**——注入指针（文件路径 + 调用链），模型仍以真实代码为唯一事实，只缩短定位延迟。

### Added

- **`scripts/knowledge.py`**（stdlib-only，新增 12 测试）：`ensure-gitignore`（保证 `knowledge-base/` 不入仓）/ `memory-rebuild`（由各知识点 frontmatter 全量重建 `MEMORY.md` 索引）/ `memory-validate`（漂移检测）。
- **`skills/specode/references/retrieval.md`**：两级 gated 检索规格 —— Tier-1 读 `MEMORY.md` 小索引按 tags+描述 匹配；命中才 Tier-2 读 ≤5 个知识点全文，用其前后端文件 + 调用链定位真实代码；含 schema↔推理 对照表与变更纪律。接入 `skills/specode/SKILL.md` 的 requirements + design phase（执行 / task-swarm 阶段零注入）。

### Changed

- **distill 重写**：从「Obsidian-primary 5 类组织器」改为「项目 `<project_root>/knowledge-base/` primary，原子 `case`/`navigation` 知识点 + `MEMORY.md` 索引」，可选复制一份到 Obsidian（绝对路径直写不拼接）。`knowledge-base/` 不提交仓库。涉及 `skills/distill/SKILL.md`、`references/{doc-template,breakdown-heuristics}.md`、`commands/distill.md`。
- **acceptance 末尾重新挂回 distill 提示**，按既有 `auto_distill` autonomous-mode default 决定是否 `AskUserQuestion`（复用既有机制，无新开关）。

### Notes

- 与 v4.0.0 被拔掉的 codemap recall 的根本区别：注入**指针非事实**、模型判断非脚本召回、默认只读小索引、命中才读且封顶 N=5。成功标准 = 定位更快/更准（token 持平亦可接受）。

## 5.0.1 (2026-06-30) — distill 收敛 md-only + 隐藏 + 全量清理 .ai-memory/codemap 残留

承接 5.0.0,把 distill 彻底收敛为「纯 md-only Obsidian 整理器」,并清掉全仓最后的记忆注入文档残留。

### Changed

- **`skills/distill/SKILL.md`**:加 `user-invocable: false` —— 斜杠菜单不再出现裸 `/distill`,也消除了「命令 + 同名可见 skill」造成的 `/specode:distill` 重复项(现只剩命令一条干净入口;Claude 仍可自动调用该 skill)。
- **distill 收敛为纯 md-only**:移除 `--format md|yml|both` flag 与 `codemap knowledge write` 写入器路径。yml 输出的唯一消费者(`codemap recall`)早在 v4.0.0 删除,yml 已无人读取,故彻底移除。

### Removed / cleaned(文档与模板里的死引用)

- **`assets/templates/requirements.md`**:删除已废弃的「## 已知约束 / 历史坑」段 —— 该段是 v4.0.0 已移除的 P3-1 codemap-recall 注入占位,SKILL 早已声明 requirements.md 不再含此段,模板未同步(会盖进每个新 spec)。
- **`skills/distill/references/doc-template.md`**:重写为 v5 md-only 模板参考 —— 删除 yml schema / `.ai-memory/knowledge/` 路径表 / codemap 写入器框架,frontmatter 对齐 SKILL 的 Obsidian 风格,保留 5 类 md 模板正文与深度标准。
- **`skills/distill/references/breakdown-heuristics.md`**:剥掉 `.ai-memory`/`codemap knowledge write`/yml 双产/supersede 框架,保留 5 维拆分方法论。
- **`commands/spec.md` / `skills/specode/references/obsidian.md` / `tests/test_project_root.py`**:`project_root` 描述去掉过时的 ".ai-memory/knowledge feeds" + "codemap recall" 消费者措辞。
- **`commands/distill.md`**:移除 `--format` flag。

全量复核:除 CHANGELOG 历史条目与「已移除 X」迁移说明外,仓库不再有把 `.ai-memory`/`codemap knowledge write`/yml-pipeline 描述成现行行为的文档。测试 233 passed。

## 5.0.0 (2026-06-30) — BREAKING: 命令去 `specode-` 前缀 + 内核 skill 隐藏

命令名 = specode 的 semver API surface。本版把命令去掉冗余的 `specode-` 前缀（插件命名空间已提供 `specode:`），并把不该被直接点的编排内核 skill 从斜杠菜单隐藏 —— 对齐 superpowers 的命名形态（无裸 `/superpowers`）。

### Changed (BREAKING — 命令重命名)

- `/specode:specode-spec` → **`/specode:spec`**（`commands/specode-spec.md` → `commands/spec.md`）
- `/specode:specode-continue` → **`/specode:continue`**（`commands/specode-continue.md` → `commands/continue.md`）
- `/specode:specode-list` → **`/specode:list`**（`commands/specode-list.md` → `commands/list.md`）
- `/specode:specode-distill` → **`/specode:distill`**（`commands/specode-distill.md` → `commands/distill.md`）
- distill skill 目录 `skills/specode-distill/` → **`skills/distill/`**，frontmatter `name: specode-distill` → `name: distill`

### Changed (斜杠菜单)

- 编排内核 skill `specode`（`skills/specode/SKILL.md`）加 `user-invocable: false` —— 裸 `/specode` 不再出现在斜杠菜单（它只应经上述命令 / 「按 spec 流程做」自然语言激活，Claude 仍可自动调用）

### Migration

- 把 `/specode:specode-X` 改成 `/specode:X` 即可，行为不变。SessionStart 提示文案、主 SKILL、references、README（EN/zh）、CLAUDE.md 已全部同步。CHANGELOG 历史条目按惯例保留旧命令名。

## 4.0.0 (2026-06-29) — BREAKING: 拔出记忆注入工程

Round 1/2 baseline 实验 (`/Volumes/External HD/Obsidian/Notes/07-Ideas/AI-Enterprise-Delivery-System/基线AB对照实验/`) 证明: 记忆注入未 net 节省 token。用户决策完全拔出, specode 专注 "spec → design → execute → acceptance 编排" 本质能力。

### Removed (specode 主 SKILL.md)

- **P3-1 codemap recall 注入段** (line 94-130): 不再调 `codemap recall ... --with-content`, requirements.md 不再含 `## 已知约束 / 历史坑` 段, 不再含 cold-start `## 相关代码地图` 段
- **P3-2 rule-acknowledgement post-check** (line 152-167): design.md 写完不再 grep `[[rule-*]]` 检查 + `AskUserQuestion` 处理偏离
- **Acceptance distill prompt sub-step** (line 179): acceptance summary 写完不再 `AskUserQuestion` 询问"是否立即沉淀"

### Preserved

- **Project-level agent docs filesystem scan** (CLAUDE.md / AGENT.md): 仍扫描 + 注入 `## 项目级约束` 段 (不涉及 `.ai-memory/`, 是纯 filesystem 扫描)
- specode 主流程 4 阶段不变 (requirements → design → execute → acceptance), 4 phase 调 superpowers 也不变
- autonomous mode 5 env (`SPECODE_INTERACTIVE` 等) 不变
- project_root frontmatter SSoT 不变

### specode-distill skill 完全重写为 v4 (md-only Obsidian organizer)

**Trigger**: 仅手动 `/specode:specode-distill <slug>`, 永不自动触发。

**Args**:
- `--target-dir <abs>` (默认 `/Volumes/External HD/Obsidian/Notes/11-KnowledgeBase/<slug>/`)
- `--format md|yml|both` (默认 `md`)

**Behavior**:
- 默认仅写 `.md` 到 `<target-dir>/<slug>/<category>/<id>.md` (Obsidian-friendly frontmatter + sections + wikilinks)
- 不调 `codemap recall` (v3 P2-2 reverse-check 已删)
- 不调 `codemap knowledge write` 默认 (仅 `--format yml|both` 时调, 写 `<target-dir>/yml-store/` 而非 spec project_root)
- 不写 `<project_root>/.ai-memory/knowledge/` (v4 完全独立于 spec 的 project_root)
- 不读 `.ai-memory/` 任何路径

### Migration

- 如需 v3 行为 (自动 recall + 自动 distill + 写 .ai-memory): `git checkout backup/specode-v3.4.0-task-swarm-v0.9.2`
- 历史 `.ai-memory/knowledge/` 内容保留不删, 用户可独立用 `codemap recall` 查询 (codemap-aimemory CLI 仍可独立装用)

## 3.3.0 (2026-06-28)

### Added — `doctor` verb in resolve_root.py (AI-EDS v0.9 痛点 #9)

新增 `resolve_root.py doctor` 子命令，检测 specode config drift：

| exit | 含义 |
|---|---|
| 0 | specsRoot 已配 + 目录存在（可能带 legacy `obsidianRoot` 警告）|
| 3 | specsRoot 未配（提示先跑 `set-root`） |
| 4 | specsRoot 配了但目录不存在（vault 被重命名 / 外置盘未挂载 / 大小写漂移 → 给出 `set-root --root <new-abs>` 可直接复制粘贴的修法）|

发现于真实试跑 2026-06-28：用户把外置盘 vault 从 `spec-in/` 重命名为 `SpecIn/`（case-sensitive 文件系统下成了两个目录），但 specode config 还指 `spec-in/`，所有下游静默走错路径。doctor 让这类漂移可一眼诊断。

### Fixed — set-root 清理 legacy obsidianRoot key (AI-EDS v0.9 痛点 #8)

`cmd_set_root` 之前只写 `specsRoot`，不删 `obsidianRoot`（specode <1.0.0 的旧 key）。读端 fallback 同时认两个键时不显问题，但其他 plugin（如 obsidian-wiki）仍直接读 `obsidianRoot` → 静默走 stale 路径，split-brain 风险（2026-06-28 真实试跑事故场景）。

修法：set-root 持久化时 `cfg.pop("obsidianRoot", None)`。doctor 在两键都存在时给 warning + 建议 re-run set-root 一次清理。

6 个 regression tests 新增 (`tests/test_set_root_cleanup_and_doctor.py`)。
specode 测试总数 27 → 33，全部通过。

## 3.2.0 (2026-06-27)

### Added — FIX-1 project_root single source of truth

`scripts/resolve_root.py` 加 3 个新 verb：

- `resolve-project-root` — 默认值推导（`git rev-parse --show-toplevel` ‖ cwd），不再要求 cwd 是 git repo（**工作区根、非 git 目录也能跑**）
- `write-project-root --spec <path> --root <abs>` — **唯一写入口**，校验绝对路径 / 目录存在 / `/Volumes` 挂载，原子写 frontmatter
- `read-project-root --spec <path>` — **唯一读入口**，缺字段 exit 3 / 值非法 exit 4

主 `SKILL.md` step 2.1/3 / `commands/specode-spec.md` step 3 / `skills/specode-distill/SKILL.md` step 1 / `references/obsidian.md` 全部改为引用这三个 verb，删除"do not ask / = cwd 不写 frontmatter"等矛盾表述。

收敛 AI-EDS ISSUE-1（文档矛盾断链）+ ISSUE-3（双写分裂）。

### Added — FIX-2 knowledge writer rewire（与 codemap-aimemory 0.4.3+ 配合）

`specode-distill` 范式翻转：从"LLM 自己写 yml"改为"LLM 产 content payload + md_body → `codemap knowledge write` 落盘"。SKILL.md / doc-template.md / breakdown-heuristics.md 全部按新流程更新。task-swarm 同样收归（见其 0.7.0）。

依赖：`codemap-aimemory >= 0.4.3`（含 `codemap knowledge` CLI）。

### Added — FIX-3d/3e consumer 更新

主 `SKILL.md` step 2.2 recall call 默认带 `--include-shared` flag（codemap-aimemory >= 0.4.4 起，opt-in 跨项目共享 knowledge）—— 未配置 `~/.config/codemap/recall.yaml shared_roots` 时是 no-op，所以**永远可以传**。

注入模板对 `source: shared` 命中加 🌐 prefix，让 reviewer 一眼区分项目本地知识 vs 团队共享知识。

依赖：`codemap-aimemory >= 0.4.4` + `codemap-semantic-index >= 0.2.0`（可选）。

## 3.1.0 (2026-06-27)

### Changed — step 2.2 injection 升级为内容摘要（P3-2 闭环 part 1）

主 `SKILL.md` step 2.2 注入命令从

```
codemap recall '<request>' --top-k 5 -o yaml
```

升级为

```
codemap recall '<request>' --top-k 5 --with-content -o yaml
```

注入格式从"wikilink 一句话摘要"升级为"完整字段表格"：

```markdown
### [[rule-coupon-mutex]] (business_rule, ranked_score=7)

**优惠券和积分互斥**

| 字段 | 值 |
|---|---|
| statement | Coupons and points can't both apply to the same order |
| why | Prevents stacking discounts beyond margin |
| exceptions | VIP ≥ 8 |
| enforcement | service layer throws / frontend disables checkbox |
```

每个 category 渲染不同字段集（rules → statement/why/exceptions/...；
pitfalls → symptom/fix/...；cases → implementation_summary/...；business
→ trigger/steps/...；modules → scope/columns/...）。

**修复闭环断点**：v3.0 注入只放了 wikilink，design phase 的 LLM
（superpowers:writing-plans / native）很可能不主动去读 yml/md，错过
关键约束。v3.1 把内容直接铺到 requirements.md 上，下游 skill 一定
能看到。

`stale` 命中（freshness_score < 0.5，由 codemap-aimemory 0.4.0 引入）
在子标题前加 ⚠️ 前缀，让用户决定是否仍要遵守过期知识。

### Added — step 3 design phase rule-acknowledgement post-check (P3-2 闭环 part 2)

`design.md` 写完后，host agent 自动扫 requirements 的
`## 已知约束 / 历史坑` 段提取所有 `[[rule-*]]`，逐一在 design.md grep
是否被显式 acknowledge 或 override。缺失时 `AskUserQuestion`：

```
设计未显式涉及以下规则，可能违背或遗漏：
- [[rule-X]] — <title>
- [[rule-Y]] — <title>

选择处理方式：
- 补充 design.md 说明如何遵守 (recommended)
- 显式声明覆盖（override rule-X: <reason>）
- 跳过（认为不适用，标记到 implementation-log）
```

用户选完后 host agent 写回 design.md 或 implementation-log。规则不再
能"悄悄遛过" design 阶段。如果 step 2.2 没召回任何 rule，post-check
自动跳过（无可校验）。

### Requirements

- **`codemap-aimemory>=0.4.0`** for `--with-content` flag + freshness
  fields. Older codemap：注入退化到 wikilink-only（v3.0 行为，依然
  能用），post-check 仍生效。

### Why this closes P3-2

P3-2 的设计目标是 "design 阶段强制规则校验"。要做到这点，前置条件
是 design phase 真的看到了规则**内容**（v3.0 wikilink-only 注入
不够）。v3.1 两个改动是缺一不可的双臂：
- step 2.2 内容注入 → 让 LLM 看见规则的具体约束
- step 3 post-check → 让"规则没被处理"不能静悄悄发生

到此 specode 闭环 "知识 → spec → design → 实施" 真正闭合。

## 3.0.1 (2026-06-26)

### Added — specode-distill step 4 pre-check (P2-2)

`skills/specode-distill/SKILL.md` step 4 now starts with a pre-step
that queries the project's existing knowledge base for relevant rules
and pitfalls **before** the LLM forms breakdown proposals:

```bash
codemap recall --from-spec "<specsRoot>/<slug>/requirements.md" \
               --project "<project_root>" \
               --types rules,pitfalls \
               --top-k 5 \
               --output json
```

Each hit is surfaced to the user as a short context bullet
`- [[<knowledge_id>]] (<type>, score=<n>) — <title> · <summary>`. The
host agent then forms proposals **with awareness of**:

- existing `rule-*` statements (don't propose contradictory new rules)
- existing `pit-*` symptoms (link via `seen_again_in` if this spec
  re-touches the same area; treat as risk if proposed code path
  matches a known failure pattern)

Proposed knowledge candidates now pre-fill `related_knowledge` with
any recall hits judged relevant.

Requires **codemap-aimemory>=0.3.6** (the `--from-spec` flag). If
`codemap recall` is unavailable (codemap-aimemory not installed or
older), the pre-step is silently skipped — proposals fall back to
spec-only context. No hard dependency.

### Why this closes P2-2

The AI-EDS roadmap defined P2-2 as "spec-distill writes rules with
awareness of historical pitfalls / cases". Until now the breakdown
step in step 4 only had the current spec's documents in context, so
the LLM had no way to know it was about to propose a rule that
contradicted last quarter's hard-won pitfall. The pre-step closes
that gap by injecting the cross-project knowledge that already lives
in `.ai-memory/knowledge/` — produced by prior runs of either
specode-distill itself or task-swarm's auto ingest.

## 3.0.0 (2026-06-26)

### Added — specode-distill 子 skill（spec-distill 迁入 specode 并改造为单 spec 模型）

specode 是 spec 全生命周期的入口（requirements → design → execute →
acceptance），把"知识沉淀"也纳入其中 → specode 成为 single source of
truth，闭环更紧。

新增 `skills/specode-distill/`：

- 5 步流程：解析 project_root → 准备 yml + md 目录 → 读 spec 全文 →
  AskUserQuestion 拆分提议 → 同时写 yml + md 双产
- 写到 spec 自己的 `project_root`（绝对路径从 `requirements.md`
  frontmatter 读），**严格 per-spec**，彻底消除原 spec-distill 跨项目
  混淆问题（一个 vault 内多项目 spec 沉到不同 project_root）
- 双产物：
  - `<project_root>/.ai-memory/knowledge/{rules,business,modules,cases,pitfalls}/*.yml`
    （机器源，给 `codemap recall` 和未来 embedding indexer）
  - `<project_root>/knowledge-base/{rules,business,modules,cases,pitfalls}/*.md`
    （人读 + embedding 源，保留散文/ascii/表格结构）
- 同 stem、同 knowledge_id；同次 LLM 一次性产 yml + md

新增 slash command：`/specode:specode-distill <slug>`。

主 SKILL.md step 6 acceptance 末尾新增 `AskUserQuestion` 提示：
*"是否立即沉淀本次需求知识？"* — "是"自动调 specode-distill；"否"输出
后续手动命令提示。不强制；refusal 不影响 spec 状态。

### Schema

5 类 yml schema + 5 类 md 模板的完整定义在
`skills/specode-distill/references/doc-template.md`：

- `rules/rule-*` — 业务规则 / 全局机制（statement / why /
  trigger_conditions / exceptions / enforcement）
- `business/biz-*` — 业务流程 / 功能页（trigger / end_state / steps
  with branches / data_flow / ui_constraints）
- `modules/mod-*` — 表 / 字段 / 调用链 / 模块地图（scope=table
  with columns/enum/shard，或 scope=call_chain）
- `cases/case-*` — 历史案例（implementation_summary / changed_files /
  key_decisions / bugs_encountered / lessons / review_findings /
  acceptance_status）每个 spec 必产 1 篇
- `pitfalls/pit-*` — 可复用坑点（symptom / root_cause / fix /
  prevention / affects / first_seen_in / seen_again_in）

### 砍掉的东西（v1/v2 spec-distill 有 → v3 没有）

| 移除 | 原因 |
|---|---|
| `scan` 子命令（vault-wide 列待沉淀） | 单 spec 模型无 "vault 全局待沉淀" 概念 |
| `<vault>/00-Index/_system/spec-distill-state.yml` | 不再需要全局 state；每个 spec 写自己项目 |
| `<vault>/00-Index/_system/spec-distill-report.yml` | 同上 |
| 按"系统"分组（`<vault>/10-Work/知识库/<系统>/`） | 替换为按"项目"分组（`<project_root>/knowledge-base/`） |
| `MEMORY.md` / `wiki-log.md` | v2 已废 |
| `--vault <path>` 标志 | 不再适用——输入只是 `<specsRoot>/<slug>/` 与 spec 自己的 `project_root` |
| Python 辅助脚本 `kn_scan.py` | 纯 LLM-driven 流程；无脚本需要 |

### Breaking changes

- **install dependency change**：obsidian-wiki **不再是 AI-EDS 工作流必装**。
  之前依赖 `/spec-distill sync` 的用户改用 `/specode:specode-distill <slug>`。
- 配套 obsidian-wiki **2.0.0** 同步移除 `skills/spec-distill/` 子目录。
- 配套 task-swarm **0.6.0** 同步加 `knowledge-base/*.md` 双产。
