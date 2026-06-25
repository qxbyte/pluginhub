---
name: spec-distill
description: >
  Distill specode-generated requirement documents under SpecIn into
  fine-grained machine-readable YAML knowledge files under each target
  project's `<project_root>/.ai-memory/knowledge/{rules,business,
  modules,cases,pitfalls}/`. Discards all Markdown outputs (no per-
  knowledge .md, no MEMORY.md, no wiki-log.md) — the AI-Enterprise-
  Delivery-System four-layer memory model treats L2 (knowledge) and L3
  (cases / pitfalls) as agent-consumable YAML alongside codemap's L1.
  Triggers: /spec-distill, /spec-distill scan, /spec-distill sync,
  "沉淀知识库", "把 spec 整理进知识库".
  SpecIn is read-only; vault writes are limited to two state files
  under `00-Index/_system/` (scan report + sync state index).
---

# spec-distill (v2 — yml-only, writes to project `.ai-memory/knowledge/`)

> **Breaking change vs v1.** v1 wrote per-system Markdown knowledge
> files + `MEMORY.md` indices under `<vault>/10-Work/知识库/<系统>/`.
> **v2 discards every `.md` knowledge output.** All knowledge now lands
> as `.yml` under `<project_root>/.ai-memory/knowledge/{rules,business,
> modules,cases,pitfalls}/`, keyed by stable IDs (`rule-*`, `biz-*`,
> `mod-*`, `case-*`, `pit-*`). The vault keeps **only** two state files
> in `00-Index/_system/`: `spec-distill-state.yml` (synced specs index)
> and `spec-distill-report.yml` (latest scan output). Per-system
> grouping is gone — each project owns its own `.ai-memory/`.

> **配置说明**：vault 的结构配置仍存在家目录注册表
> `~/.config/obsidian-wiki/configs/<库名>.json`（按 active 库解析；未注册
> 则回退库内 `<vault>/.wiki/config.json`）。schema 见本插件根
> `config.example.json`。脚本仍通过 `--vault "<vault 根路径>"` 指定 vault。
>
> **脚本定位（插件）**：脚本随插件安装，运行前先解析插件根 `$WIKI`：
> ```bash
> WIKI="${CLAUDE_PLUGIN_ROOT:-${CODEBUDDY_PLUGIN_ROOT:-}}"; [ -d "$WIKI/skills/spec-distill" ] || WIKI="$(find "$HOME/.claude/plugins/cache" "$HOME/.codebuddy/plugins/cache" "$HOME/.copilot/installed-plugins" -type d -path '*/obsidian-wiki/skills/spec-distill' 2>/dev/null | sort -V | tail -1 | sed 's:/skills/spec-distill$::')"
> ```
> 下文命令里写的 `scripts/kn_scan.py` 一律指 `"$WIKI/skills/spec-distill/scripts/kn_scan.py"`。

---

## 命令表

| 命令 | 行为 |
|---|---|
| `/spec-distill`（= `scan`） | 跑 `python3 scripts/kn_scan.py scan`，读 `00-Index/_system/spec-distill-report.yml`，汇报待沉淀清单并提议先做哪个；**不写知识 yml** |
| `/spec-distill scan [--source <路径>] [--vault <路径>]` | 同上，可手动指定 spec 源目录或 vault 根 |
| `/spec-distill sync [--source <路径>] [--spec <名>] [--project <abs path>] [--rescan] [--dry-run]` | 按 spec 维度沉淀知识到目标项目（见 §sync 逐 spec 流程），LLM 驱动，用户控节奏 |
| `/spec-distill help` | 显示本命令表与流程说明 |

> **重要区分**：`scan` 是脚本子命令（`kn_scan.py scan`），可直接运行；
> `sync` **不是**脚本子命令——它是本 SKILL.md 编排的 LLM 交互工作流，
> 不得向脚本传入 `sync` 参数。

未给子命令时按 `scan` 处理。

---

## scan 流程

1. 运行脚本：`python3 "$WIKI/skills/spec-distill/scripts/kn_scan.py" scan --vault "<vault>" [--source <路径>]`
   - `--vault` 必填（脚本经 `load_config` 按该路径在家目录注册表取配置，未注册则回退 `<vault>/.wiki/config.json`）。
   - 源目录默认 `<SpecInRoot>/windows-Public/specs/`；`SpecInRoot` 自动探测 `SpecIn/`（无则 `spec-in/`）。
2. 脚本逻辑：
   - 列 `<source>/*` 下所有 spec 目录。
   - 读 `<vault>/00-Index/_system/spec-distill-state.yml` 拿已 sync 的 `spec_id` 集合。
   - pending = 源目录 spec - state 中的 spec；done = 交集。
   - 写 `<vault>/00-Index/_system/spec-distill-report.yml`（覆盖式，纯机器可读）。
3. 向用户汇报：
   - 待沉淀 spec 列表（spec_id + 目录名）。
   - 已沉淀 spec 列表（spec_id → project_root → synced_at）。
   - 提议优先处理哪个 spec（按工作项目特征判断，跳过个人/测试项目）。

---

## sync 逐 spec 流程

对每个待沉淀 spec，按以下六步顺序执行。**不可省略任何一步。**

### 第 1 步：解析 project_root

按优先级（前者赢）：

1. CLI `--project <abs path>` 显式覆盖
2. 读 `<source>/<spec>/requirements.md` 顶部 YAML frontmatter 中的 `project_root` 字段（specode v2 写入）
3. 都没有 → **报错并请求用户用 `--project` 重跑**。不得猜测。

校验：必须是绝对路径，且目录存在；否则报错。

### 第 2 步：准备目标目录

```bash
mkdir -p "<project_root>/.ai-memory/knowledge/"{rules,business,modules,cases,pitfalls}
```

如目录已存在，跳过。如同一 project 已被其它 spec sync 过，会出现其它 .yml — **不动这些已有文件**（只追加本次 spec 的 .yml；同名 ID 冲突走第 5 步规则）。

### 第 3 步：读全 spec

Read 该 spec 目录下所有 `.md` 文件：`requirements`、`design`、`tasks`、`implementation-log`、`bugfix`、`acceptance-checklist`、测试报告等。子目录限 3 层深。

### 第 4 步：AskUserQuestion — 提议知识点拆分（不可跳过）

按 `references/breakdown-heuristics.md` 中的启发式（5 维 → 5 类目录映射），输出 N 个候选知识点，每个包含：

- **category**: `rules` / `business` / `modules` / `cases` / `pitfalls`
- **knowledge_id**: `<prefix>-<kebab-slug>`（`rule-` / `biz-` / `mod-` / `case-` / `pit-`）
- **拟标题**（中文）、**一句摘要**、**拟 tags**

**AskUserQuestion 让用户确认/增删/合并/改名/改归属**，拿到最终列表后再进行下一步。
不得自动跳过此确认步骤。

### 第 5 步：逐篇写 yml 文档

每个用户确认的知识点，按 `references/doc-template.md` 模板中对应类型的 yml schema 写一篇：

- 路径：`<project_root>/.ai-memory/knowledge/<category>/<knowledge_id>.yml`
- 必填字段（5 类公共）：
  - `schema_version: "1.0"`
  - `knowledge_id`（同文件名 stem，不带 `.yml`）
  - `type`（与 category 一一对应）
  - `created_at` / `updated_at`（ISO date）
  - `source_spec`（绝对路径或相对 vault 的 spec 目录）
  - `source_files`（list of relative paths under spec dir）
  - `related_requirements`（list of req-id 字符串）
  - `related_code`（list of file/entity refs；如无信息留 `[]`）
  - `confidence`（high / medium / low）
  - `status`（active / deprecated / draft）
- 类型特异字段：详见 `references/doc-template.md`。
- 文件名冲突（同 category 已有同 ID）：Read 原文 → 比对差异 → 增量更新 `updated_at` + `related_requirements` 追加本次 spec → 必要时升 `version` 字段。

### 第 6 步：更新 vault state（必做）

追加到 `<vault>/00-Index/_system/spec-distill-state.yml`：

```yaml
synced:
  <spec_id>:
    project_root: <abs path>
    synced_at: 2026-06-25T16:00:00Z
    new_count: <本次新建的 .yml 篇数>
    updated_count: <本次更新的 .yml 篇数>
```

存在则更新该 spec_id 对应的条目；不存在则新增。

---

## 五维启发式 → 五类目录映射

| 启发式维度 | 目录 | ID 前缀 | type 字段 |
|---|---|---|---|
| 机制 / 规则 | `rules/` | `rule-` | `business_rule` |
| 业务流程 / 功能页 | `business/` | `biz-` | `business_process` |
| 表 / 字段 / 调用链 | `modules/` | `mod-` | `module_map` |
| 历史需求实现案例 | `cases/` | `case-` | `case` |
| 坑点 / 失败修复 | `pitfalls/` | `pit-` | `pitfall` |

> 一个 spec 通常产出 cases 1 篇（必有，记录本次实现）+ 可选 0-N 篇 rules / business / modules / pitfalls。若 `implementation-log.md` / `bugfix.md` 含可复用坑点 → 单独拎出 `pit-*.yml`，不要塞到 case 内。

---

## 红线

以下规则**不可绕过**：

| 红线 | 说明 |
|---|---|
| SpecIn 只读 | 永不修改/移动/重命名 SpecIn 下任何文件 |
| 可写目录（仅两处） | (a) `<project_root>/.ai-memory/knowledge/` 下的五类目录及其 `.yml`；(b) `<vault>/00-Index/_system/spec-distill-{state,report}.yml`。**vault 其它任何路径只读**，不得再写 `10-Work/知识库/`、`MEMORY.md`、`wiki-log.md` |
| 不写 .md | spec-distill v2 不写任何 `.md` 知识文档；旧版的 `MEMORY.md` / `wiki-log.md` / `per-knowledge.md` 全部废弃。给人看的索引通过 Obsidian 渲染 `.yml` 或上游 codemap-aimemory 的产物 |
| 敏感信息拦截 | 遇账号/明文 token/密钥/人员姓名+联系方式 → AskUserQuestion 列出原文位置，由用户决定纳入/脱敏/跳过 |
| 改前必读 | 写任何已存在的 `.yml` 前先 Read 其全文 |
| 批量写前备份 | 同 project 批量写多篇 yml 前，tar 备份 `<project_root>/.ai-memory/knowledge/` 到 `~/Library/Caches/spec-distill-backup-<ts>/`（Windows 退化为同盘临时目录） |
| 写后追加状态 | 每次 sync 后 append `<vault>/00-Index/_system/spec-distill-state.yml` |
| 外置盘检查 | vault 或 `project_root` 路径含 `/Volumes/` 时，先确认挂载（`ls "/Volumes/External HD"` 能访问）；失败则报错停止，不静默写到其他位置 |
| 不联网 | 本 skill 全程不访问网络 |

---

## 跨平台

- `--project` 必须是绝对路径，跨平台一律按 OS 风格校验存在性。
- 源目录自动探测 `SpecIn/`（无则 `spec-in/`），兼容 Windows 上仍叫 `spec-in/` 的库。
- 脚本 `kn_scan.py` 使用 Python 标准库 + UTF-8；不依赖外部包；yaml 输出走纯字符串拼接（不依赖 PyYAML，避免装包），但读取可选 PyYAML 优雅降级。

---

## 与其它 skill 的关系

- **独立 skill**，与 `wiki-struct`（结构层）、`wiki-curate`（方法论伞 + 内容向 ingest/curate/lint）并列，各管一摊。
- v1 中"按系统归属"概念在 v2 中**移除**：知识不再按"系统名"分组，每个 project 一份独立的 `.ai-memory/knowledge/`。多 project 共享 vault 时通过 `spec_id` 在 state 中全局去重。
- **接入四层记忆模型**：
  - **L0 / L1** 由 `codemap-aimemory>=0.3.2`（PyPI）在 `<project_root>/.ai-memory/` 下写 `project.yml` + `entities/` + `relations/`，每次 `codemap index` 重算。
  - **L2 / L3** 由本 skill 写 `.ai-memory/knowledge/{rules,business,modules,cases,pitfalls}/`，按 spec 累加。
  - 两者共用同一 `<project_root>/.ai-memory/` 根目录但目录互不重叠，Agent 一次性 mount 全四层。
- 旧 `kn-indexer` 已退场（v1 接管），本 v2 进一步把"维护人类索引"的职责一并下线。

---

## References

- `references/breakdown-heuristics.md` — 知识点拆分启发式（5 维 → 5 类目录）
- `references/doc-template.md` — 5 类 yml schema 模板
