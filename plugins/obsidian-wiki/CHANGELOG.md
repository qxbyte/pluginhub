# Changelog — obsidian-wiki

obsidian-wiki 是维护 Obsidian LLM-Wiki 的多 agent 插件（从独立 skills 仓迁入并重打包）。本文件记录其自身版本。

## Unreleased

## 2.2.1 (2026-07-21) — 修 Kimi 市场 schema + Kimi 工具映射

随 pluginhub Kimi 安装修复同发：`.kimi-plugin/marketplace.json` 改 Kimi 官方 schema（`version:"2"`/`id`/`source` 指向各插件子目录，本地 clone 可装）；`.kimi-plugin/plugin.json` 加 `skillInstructions`（把 `AskUserQuestion` 等映射到 Kimi 工具，并重申只读目录/受管块红线）。obsidian-wiki 无 hooks，故不加 `sessionStart`。README Kimi 安装说明改为本地 clone。仍未真机验证。

## 2.2.0 (2026-07-20) — 多宿主适配：skills 去宿主绑定 + CodeBuddy/Codex/Kimi 独立 manifest

obsidian-wiki 现在同时面向 Claude Code / CodeBuddy / Codex / Kimi 四个宿主。

- **skills prose 去宿主绑定**：三个 skill（wiki-struct / wiki-curate / wiki-orchestrate）顶部各加一条「Host-tool convention」——`AskUserQuestion` 工具名**照旧保留**（对有它的宿主最可靠），补兜底：宿主缺该工具时用最近的结构化提问工具，都没有则降级为纯文本提问。`wiki-curate` 里「只用本机 Claude Code 上下文」等绑定单一宿主品牌的表述改为「只用本机 agent 上下文」。`AGENTS.md` 的宿主列举扩展为「Claude Code / Copilot CLI / CodeBuddy 及其它兼容 Agent-Skills 的 CLI」。作为**笔记内容示例**出现的模型名（如 “Claude 3.5”）与目录名（`.claude`）保持不改。零行为变化、红线不变。
- **新增三宿主独立 manifest**：`.codebuddy-plugin/plugin.json` + `.codex-plugin/plugin.json` + `.kimi-plugin/plugin.json`（本插件无 hooks），及三份根 catalog。Codex/Kimi 的 schema 待实测（见 README 标注）。

## 2.1.0 (2026-07-08) — resolver 回归相对路径 + description 朴素化

与同源发布的 ragkit 0.1.7 / specode 6.2.0 / task-swarm 0.11.0 一致，把脚本定位从旧 resolver 回归 superpowers 相对路径范式。旧 resolver（`WIKI="${CLAUDE_PLUGIN_ROOT:-${CODEBUDDY_PLUGIN_ROOT:-}}"` + `find … | sed`）在 Windows 下 `${VAR:-...}` 被 host 插值器吞成空、CodeBuddy 不注入这些环境变量，必然解析失败。

- **三个 skill（wiki-struct / wiki-curate / wiki-orchestrate）的脚本定位**：删掉 `${VAR:-...}` + `find` 缓存的 resolver 段，改为用本 skill 的 **base directory 相对路径**跑脚本——同 skill 自带脚本用 `scripts/xxx.py`（如 `python3 scripts/struct_gen.py check`），插件根通用库用 `../../lib/registry.py`。wiki-orchestrate 因跑兄弟 skill 的脚本，用 `../wiki-struct/scripts/struct_gen.py`、`../wiki-curate/scripts/lint.py`。同步清理各 skill `references/` 里的旧写法（`sub-skills.md`、`dir-config.md`）。根治 Windows `:-` 吞空 / CodeBuddy 不注入变量。
- **AGENTS.md 总纲**：本文件不是 skill、没有 base directory，不能用裸相对路径。「跑脚本」「首次配置」两段删掉 resolver bash，改为**指向对应 skill**（脚本在 skill 上下文里以相对路径运行），只保留语义说明与参数示例。
- **wiki-orchestrate description**：由 `>` block scalar（折叠标量，多行）改为**朴素单行 plain scalar**（无引号、无半角 `: `），防 CodeBuddy YAML 解析对 block scalar 兼容性问题导致坍缩。中文内容语义不变。

零行为变化（脚本本身、命令、红线均未改），仅脚本定位方式与 YAML 形态调整。

## 2.0.4 (2026-07-06) — skill description 统一模板

- 三个 skill（wiki-struct / wiki-curate / wiki-orchestrate）的 frontmatter `description`（渐进式加载唯一常驻的元数据）统一为「用途开头 → 做什么 → 触发语 → 边界/交叉引用」轻量模板：补上彼此的交叉引用边界（结构层→wiki-struct、内容策展→wiki-curate），删去版本史噪音（如 wiki-curate 的「v2.0.0 剥离」）。零行为变化。

## 2.0.3 (2026-07-05) — Discover 分类标签

- marketplace.json 加 `"category": "productivity"`，Discover 面板显示 `[productivity]` 标签。零行为变化。

## 2.0.2 (2026-07-05) — description 收敛为当前说明

- `description` 字段（marketplace.json + plugin.json）清掉累积的版本 blurb，收敛成一句话讲插件当前干嘛（三个 skill：wiki-struct / wiki-curate / wiki-orchestrate）；版本历史只留在本 CHANGELOG。README 徽章 + 表格行同步。零行为变化。

## 2.0.1 (2026-07-02) — 清理 spec-distill 剥离后的文档残留

### Fixed — 清理 2.0.0 spec-distill 剥离后的文档残留

2.0.0 删除了 `skills/spec-distill/`（含 `kn_scan.py`），但大量文档没同步：
`wiki-orchestrate` 仍会尝试运行已不存在的 `kn_scan.py`，README / AGENTS 仍宣传
「四个 skill」。本次全部对齐到三 skill 现实：

- `README.md` / `AGENTS.md`：「四个 skill」→「三个 skill」，删 spec-distill 行与
  `kn_scan.py` 调用示例，补「已剥离、迁往 specode `/specode:distill`」迁移说明。
- `wiki-orchestrate/SKILL.md`：编排序「结构→沉淀→策展」→「结构→策展」；体检从
  三方改两方（删 `kn_scan.py` 调用与 spec-distill-report）；删「知识沉淀」执行阶段、
  wiki-log 行模板与 `knowledge.spec_in_candidates` 残留。
- `wiki-orchestrate/references/sub-skills.md`：删 §2 spec-distill 整节（wiki-curate
  升为 §2），「三个」→「两个」。
- `wiki-orchestrate/references/decision-guide.md`：删 kn_scan 信号行、「知识沉淀」
  默认阶段与「项目落哪个系统」判断点。
- `wiki-curate/SKILL.md` + references（writing-conventions / note-templates /
  readonly-dirs-policy / karpathy-llm-wiki）、`wiki-struct/SKILL.md`：spec-distill
  职责描述改为「遗留产物只读；新沉淀走 specode `/specode:distill`」，并删除指向已
  删除文件（`spec-distill/references/*.md`）的死链接。

## 2.0.0 (2026-06-26)

### BREAKING — spec-distill 已剥离

spec-distill 作为 "对接 specode 沉淀知识"的工具，本质不属于"Obsidian
vault 维护"工具集，曾在 v1/v2 期间临时寄放在本插件内。v2.0 将其完整
迁移到 **specode 内子 skill specode-distill**（slash command 改为
`/specode:specode-distill <slug>`），并对触发模型做了根本性调整：
单 spec 触发、写到 spec 自己的 project_root，彻底消除 v1/v2 spec-distill
依赖 vault 全局 scan 时的跨项目混淆问题。

obsidian-wiki **本体仍然存在**，剩余三件套：

- `wiki-struct` — 维护 Obsidian Home 树 / 各一级目录 README / 00-Index
  分区页的受管块
- `wiki-curate` — Karpathy 方法论的内容向 ingest / curate / lint
- `wiki-orchestrate` — 只读体检 → 行动计划 → 编排上面两个

如果你之前依赖 v1/v2 spec-distill：

1. 安装最新 specode 3.0+（`/plugin install specode`）。
2. 用 `/specode:specode-distill <slug>` 替代 `/spec-distill sync`。
3. 知识不再写到 `<vault>/10-Work/知识库/<系统>/`，而是写到每个 spec
   的 `<project_root>/.ai-memory/knowledge/` + `<project_root>/knowledge-base/`。
4. vault 内 `00-Index/_system/spec-distill-state.yml` 与
   `spec-distill-report.yml` 不再被维护——可以保留作为历史档案，也
   可以删除。

### 移除

- `skills/spec-distill/`（整个子目录）
- `scripts/kn_scan.py`（连同 17 个单测）— 单 spec 模型不需要全局扫描

## 1.1.0 (2026-06-25)

### BREAKING: spec-distill 完全重写输出层（v2）

为接入 AI-Enterprise-Delivery-System 四层记忆模型（L0/L1 由
`codemap-aimemory>=0.3.2` 在 `<project_root>/.ai-memory/` 下写；L2/L3
由本 skill 写），spec-distill 抛弃所有 markdown 输出，改产纯 yml 知识：

- **目标位置**：`<project_root>/.ai-memory/knowledge/{rules,business,
  modules,cases,pitfalls}/<id>.yml`（不在 vault 内，不再按"系统"分层）。
- **废弃产物**：v1 的 `10-Work/知识库/<系统>/<知识点>.md` /
  `MEMORY.md` / `00-Index/_system/wiki-log.md` 一律不再写。
- **vault 内仅保留两个状态文件**：
  - `00-Index/_system/spec-distill-state.yml` — sync 完成后追加的已沉淀
    spec 索引（`{spec_id: {project_root, synced_at, new_count}}`）。
  - `00-Index/_system/spec-distill-report.yml` — scan 命令覆盖式产出
    （pending / done 列表 + counts）。

### sync 流程变化

- **project_root 解析**：优先级 `--project <abs>` → spec 的
  `requirements.md` 顶部 YAML frontmatter `project_root` 字段（由 specode
  v2 写入）→ 报错请求用户指定。**不再猜测**。
- **拆分启发式 → 五类目录映射**（5 维 + cases/pitfalls 额外两类）：
  - 业务流程 / 功能页 → `business/biz-*.yml`
  - 表/字段 / 调用链 → `modules/mod-*.yml`
  - 机制 / 规则 → `rules/rule-*.yml`
  - 本次实现（每个 spec 必产 1 篇）→ `cases/case-*.yml`
  - 可复用坑点 → `pitfalls/pit-*.yml`
- 同 ID 升级规则：`updated_at` 推进、`version` +1、`related_requirements`
  追加；不重写已有结构性字段。

### references 重组

- `references/doc-template.md` — 完全重写为 5 类 yml schema 模板
  （公共字段 + 类型特异字段）。
- `references/breakdown-heuristics.md` — 5 维启发式保留，开头加 5 维 → 5
  类目录映射表，"拆分流程"步骤补 `category` + `knowledge_id` 要求。
- `references/memory-rules.md` — **删除**（不再维护 MEMORY.md）。

### scripts/kn_scan.py 重写

- 抛弃 v1 的"读各系统 MEMORY 表反向解析"逻辑。
- 改为读 `<vault>/00-Index/_system/spec-distill-state.yml`（JSON-as-YAML，
  零外部依赖），与 SpecIn 源目录做差集得 pending / done。
- 输出 `spec-distill-report.yml`（之前是 `.md`）。
- 17 个新单测覆盖 discovery / state / scan / report 四组路径，全部通过。

### 配合 specode 改造

本 PR 同步更新 specode v2.0.0（plugin.json 不变）：

- `assets/templates/requirements.md` 顶部加 YAML frontmatter，含
  `spec_id` / `project_root` / `created_at`。
- `skills/specode/SKILL.md` "requirements" phase 流程：写 requirements.md
  前必须用 `AskUserQuestion` 让用户确认 `project_root`（默认 `git
  rev-parse --show-toplevel` 或 cwd），把确认值写入 frontmatter；下游
  spec-distill v2 从此 frontmatter 读 `project_root`。

## 1.0.1 (2026-06-20)

首个发布。维护 Obsidian LLM-Wiki（Karpathy 方法论：Sources 只读 / Wiki LLM 写 / Schema 规约）的四个 skill + 家目录多库配置注册表。

### 四个 skill（`skills/`）

- **wiki-struct** — 确定性重写 Home 总览树 / 各一级目录 README / `00-Index` 分区页的"受管块"（只改 marker 之间），产出结构体检报告。
- **spec-distill** — 把 SpecIn 里 specode 生成的需求文档逐项目提炼成细粒度知识库笔记（`10-Work/知识库/<系统>/`）并维护 MEMORY；替换原 kn-indexer，跨平台。
- **wiki-curate** — 内容向 ingest / curate / lint + Karpathy 三层方法论 doctrine（写作规范、只读红线、笔记模板）。
- **wiki-orchestrate** — 统一编排：只读体检 → 行动计划 → 按「结构 → 沉淀 → 策展」调用上面三个。

### 设计

- **代码通用、零结构硬编码**：每个库的结构配置存**家目录多库注册表** `~/.config/obsidian-wiki/`（`vaults.json` 记各库 path+active，`configs/<名>.json` 存结构），按 vault keying；未注册则回退库内 `<vault>/.wiki/config.json`。
- `lib/registry.py`：`list` / `resolve` / `register` / `set-active`；`$OBSIDIAN_WIKI_CONFIG_DIR` 可覆盖配置根。
- 脚本 Python 3 标准库、UTF-8、零外部依赖；`--vault` 必填；共享 `lib/wikicommon.py`。
- **多 agent**：Claude Code / Copilot CLI / CodeBuddy 原生发现 `skills/`；Codex CLI 走根 `AGENTS.md`（脚本照跑，LLM 流程内联读 SKILL.md）。
- 全 5 套件单测通过；家目录配置与库内回退等价性已验证。
