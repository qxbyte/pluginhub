<p align="right"><a href="./README.md">English</a> | <strong>中文</strong></p>

# pluginhub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./README.zh-CN.md#许可证)
[![specode](https://img.shields.io/badge/specode-6.5.1-blue.svg)](./plugins/specode/.claude-plugin/plugin.json)
[![task-swarm](https://img.shields.io/badge/task--swarm-0.12.2-blue.svg)](./plugins/task-swarm/.claude-plugin/plugin.json)
[![obsidian-wiki](https://img.shields.io/badge/obsidian--wiki-2.2.1-blue.svg)](./plugins/obsidian-wiki/.claude-plugin/plugin.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2)](https://github.com/qxbyte/pluginhub#installation)
[![CodeBuddy](https://img.shields.io/badge/CodeBuddy-2.97.1%2B-1E90FF)](https://github.com/qxbyte/pluginhub#installation)
[![Tests](https://img.shields.io/badge/pytest-301%20cases-success)](./plugins/task-swarm/tests)

> qxbyte 面向 CLI 编码代理（Claude Code / CodeBuddy / Codex / Kimi）的插件 marketplace。

**pluginhub** 是一个插件 marketplace：`marketplace add` 一次，之后即可安装其中任意插件。后续会有更多插件加入。

## 插件一览

| 插件 | 版本 | 做什么 |
| --- | --- | --- |
| **specode** | 6.5.1 | 轻量**规格驱动工作流**编排外壳——带 host agent 走 requirements → design → tasks → 执行 → 验收，每阶段委托给 [superpowers](https://github.com/obra/superpowers) 技能（一等公民 specode 原生降级），每条规格固定产出 4 份文档（requirements / design / tasks / implementation-log）。内置独立 `intake` 与 `execute` skill（执行尾段可随时手动 `/specode:execute` 触发）、零 import 的 task-swarm 并发执行衔接、可选的定位型经验检索。版本历史见 [CHANGELOG](./plugins/specode/CHANGELOG.md)。 |
| **task-swarm** | 0.12.2 | 由 `pipeline.yml` 驱动的独立**多 agent 编排**——语义任务组 + 跨组并发、fork coder、按组 reviewer + validator 循环（`state.json` 为单一事实源）。specode 把执行阶段委托到这里；也可用 `/task-swarm:swarm` 直接独立运行。详见 [`plugins/task-swarm/`](./plugins/task-swarm) 及其 CHANGELOG。 |
| **obsidian-wiki** | 2.2.1 | 用三个 skill 维护 Obsidian LLM-Wiki——确定性结构层（`wiki-struct`）、内容策展（`wiki-curate`）、统一编排器（`wiki-orchestrate`）。通用代码 + 按库配置放在家目录注册表 `~/.config/obsidian-wiki/`（回退 `<vault>/.wiki/config.json`），零硬编码结构。详见 [`plugins/obsidian-wiki/`](./plugins/obsidian-wiki)。 |
| **ragkit** | 0.2.2 | 独立知识库 **RAG**——向量 + 词汇 + 元数据三路召回，RRF 融合，返回定位卡片。specode `distill` 产出的 `knowledge-base/` 可直接消费；零重型依赖（词汇路仅需 stdlib + numpy）。详见 [`plugins/ragkit/`](./plugins/ragkit)。 |

`## 安装` 覆盖整个 marketplace；其余章节（能力亮点、使用、项目结构）记录的是 **specode**（旗舰插件）。**task-swarm** 的文档见 [`plugins/task-swarm/`](./plugins/task-swarm) 下的源码与 `CHANGELOG`；**obsidian-wiki** 的文档见 [`plugins/obsidian-wiki/`](./plugins/obsidian-wiki) 下的 `README.md` / `AGENTS.md`。

## 能力亮点

- **编排外壳，不是重型引擎。** specode 把每个阶段委托给成熟的 superpowers 技能（`brainstorming` → `writing-plans` → `subagent-driven-development` / `executing-plans` → `verification-before-completion`），自身只管规格生命周期、文档落盘和 task-swarm 衔接。
- **原生降级，一等公民。** 没有 superpowers？specode 用 `AskUserQuestion` 向导 + 顺序 TDD 自己跑澄清 / 规划 / 执行 / 验收循环，原生路径与 superpowers 路径地位相同，不是凑数的备选。
- **4 份固定文档，固定命名，固定位置。** 每条规格产出 `requirements.md` / `design.md`（传统设计文档：架构 / 模块 / 接口 / 数据流）/ `tasks.md`（可执行计划，引擎中立）/ `implementation-log.md`，统一落在 `<specsRoot>/<slug>/` 下，无论用哪种引擎生成内容。缺陷修复用 `requirements.md` 散文描述，不单独建 `bugfix.md`。
- **文档即状态。** 无持久状态文件，无锁，无状态行 footer，无日志。"我在哪个阶段？"由已存在的文档以及 `tasks.md` 中 `- [ ]` 勾选进度推断得出（5.x 存量 spec 看 `design.md`）。
- **单一自适应选择器。** `tasks.md` 确认后，`AskUserQuestion` 选择器动态呈现最多 4 条执行路径——仅展示当前已安装引擎对应的选项：委托 task-swarm / superpowers subagent-driven / superpowers executing-plans / specode 自执行。
- **首次使用问一次目录。** 第一次使用时，specode 询问你的文档管理目录，将其**原样**作为规格根目录持久化到 `~/.config/specode/config.json.specsRoot`，之后不再询问。
- **单个轻量 hook。** 仅一个 `SessionStart` 提醒式 hook，告知代理 specode 可用，不阻断，无逐轮机制。
- **并发执行是独立插件。** 选"委托 task-swarm"后，specode 读取 `tasks.md` 派生 `pipeline.yml`，零 import 衔接独立的 **task-swarm** 插件。
- **项目级约束沿链路传递。** specode + task-swarm（AI-EDS v0.9 痛点 #14 方案 D，保留至 v4.0.0 / v0.10.0）扫 `<project_root>` 根 / 直接父目录 / 任何被 `@writes` 触达的子目录里的 `CLAUDE.md` / `AGENT.md` / `AGENTS.md` / `CODEBUDDY.md`，把命中的**绝对路径**（不复制内容）同步注入 `requirements.md` 的「## 项目级约束」段 + 每个 coder / reviewer / validator `task.md` 的「## 项目级约束（必读）」段。`_PROJECT_AGENT_DOCS.md` inbox sentinel 强化硬约束。修掉「独立 subagent 进程看不到主 agent 自动加载的指南文件」这个静默漏点。
- **只有两个输入，别无配置。** specode 唯一的持久状态就是 specsRoot 配置（`~/.config/specode/config.json`，或 `SPECODE_ROOT` env 覆盖）+ 每个 spec 的 `project_root`（写在其 `requirements.md` frontmatter，作为下游各步读取的唯一真实源）。没有 defaults 文件、没有 autonomous-mode 环境变量旋钮——每个 `AskUserQuestion` 门就是直接问。
- **定位型知识，而非记忆注入。** AI-EDS 时代的记忆注入管线（specode P3-1 `codemap recall` + P3-2 rule-check + acceptance auto-distill，加 task-swarm `cmd_resolve` auto-ingest 写 `.ai-memory/knowledge/*.yml`）在 baseline 实验（3 case）证明 recall 注入未 net 节省 token 后于 v4.0.0 / v0.10.0 完全移除，两插件都不读写 `.ai-memory/knowledge/`。**v5.1.0 以「定位用·非事实用」的全新路线重新引入检索**：手动跑 `/specode:distill <slug>` 把原子 case / navigation 知识点沉淀到项目自己的 `<project_root>/knowledge-base/`（gitignored，可选复制到你指定的 Obsidian 目录）；requirements / design 阶段对其小索引 `MEMORY.md` 跑两级 gated 检索、只注入定位指针——真实代码始终是唯一事实来源，执行 / task-swarm 阶段零注入。如需 v3.4.0 / v0.9.2 行为：`git checkout backup/specode-v3.4.0-task-swarm-v0.9.2`。

## 安装

> 📌 **marketplace 的名字是 `pluginhub`（仓库名），不是 `qxbyte`（owner 名）。**
> 所有安装 / 卸载命令都用 `<plugin>@pluginhub`（如 `specode@pluginhub` / `task-swarm@pluginhub`）。写成 `@qxbyte` 会报 `Marketplace "qxbyte" not found`。本地 cache 路径也按 marketplace 名挂在 `~/.claude/plugins/cache/pluginhub/<plugin>/<version>/`——排查"装了哪个版本"时常用到。

### GitHub（推荐）

支持四个宿主。**Claude Code** 与 **CodeBuddy** 已支持并验证（CodeBuddy 已在
2.97.1 上验证）；**Codex** 附带实验性 manifest，安装语法尚未实测；**Kimi Code**
**只能本地 clone 安装**（无法从 URL 装 monorepo 插件）——详见下方
[Kimi Code（本地安装）](#kimi-code本地安装)与 [多宿主支持](#多宿主支持)。

```sh
# Claude Code
claude plugin marketplace add https://github.com/qxbyte/pluginhub
claude plugin install specode@pluginhub

# CodeBuddy
codebuddy plugin marketplace add https://github.com/qxbyte/pluginhub
codebuddy plugin install specode@pluginhub

# Codex（schema 已按官方文档改对；尚未在真机 Codex 跑过）
codex plugin marketplace add qxbyte/pluginhub
codex plugin add specode@pluginhub        # 注意是 `plugin add`，不是 `install`

# Kimi Code —— 不是 URL 安装；见下方「Kimi Code（本地安装）」。
```

如需完整的 superpowers 加持体验，请额外安装 **superpowers** 插件。如需多 agent 并发执行，请从同一 marketplace 额外安装 **task-swarm**（**无需**再 `marketplace add`）——装了它 specode 会在执行阶段委托给它，没装则 specode 顺序自执行：

```sh
# Claude Code
claude plugin install task-swarm@pluginhub
# CodeBuddy
codebuddy plugin install task-swarm@pluginhub
```

specode 不依赖这两者，原生降级路径开箱即用。

### Kimi Code（本地安装）

Kimi Code **无法从 GitHub URL 安装 pluginhub**——裸仓库 URL
（`/plugins install https://github.com/qxbyte/pluginhub`）和远程 marketplace URL
（`/plugins marketplace https://…/marketplace.json`）**都不行**：Kimi 不支持从
monorepo **子目录**安装插件，其扫描只认单个顶层插件目录（据 Kimi 官方文档 + 源码
确认）。请改用**本地 clone** 安装：

```sh
# 1) 任意位置 clone，记下 clone 的绝对路径。
git clone https://github.com/qxbyte/pluginhub

# 2) 在 Kimi 会话里，按【绝对路径】逐个安装你要的插件：
/plugins install /绝对路径/pluginhub/plugins/specode
/plugins install /绝对路径/pluginhub/plugins/task-swarm
/plugins install /绝对路径/pluginhub/plugins/ragkit
/plugins install /绝对路径/pluginhub/plugins/obsidian-wiki

#    …或用本地 marketplace 文件浏览四个再装：
/plugins marketplace /绝对路径/pluginhub/.kimi-plugin/marketplace.json

# 3) 开新会话——Kimi 只在【新会话】加载插件变更。
/new
```

- 路径**必须是绝对路径**；相对路径会报 `Plugin root must be an absolute path`。
- Kimi 安装时会把插件**拷贝**进它的托管目录，所以 `git pull` 更新后需**重装**才生效。
- Kimi 下 specode/ragkit 的会话提示由各 manifest 的 `sessionStart.skill`
  （`using-specode` / `using-ragkit`）注入——没有 `SessionStart` hook；task-swarm /
  obsidian-wiki 无会话提示（skills 仍靠 Kimi 原生扫描发现）。
- 未来的「远程一键装」需给每个插件挂 release zip 资产（Kimi 接受 zip-URL 作为
  source）——尚未搭建。
- **已在真机 Kimi 验证**：本地 **marketplace 浏览**安装
  （`/plugins marketplace <abs>/.kimi-plugin/marketplace.json`）成功，`/specode:spec`
  能触发 specode。**尚未确认**：`sessionStart.skill` 自动提示（目前是手动打命令触发的，
  不是模型主动知道）、以及其余三个插件的端到端流程。

### 一次性会话（仅 Claude Code）

```sh
claude --plugin-url https://github.com/qxbyte/pluginhub/archive/refs/heads/main.zip
```

### 本地开发

```sh
git clone https://github.com/qxbyte/pluginhub.git
claude    --plugin-dir ./pluginhub/plugins/specode
codebuddy --plugin-dir ./pluginhub/plugins/specode

# 想用委托式多 agent 执行就把 task-swarm 也挂上
claude --plugin-dir ./pluginhub/plugins/specode --plugin-dir ./pluginhub/plugins/task-swarm
```

### 卸载

```sh
claude plugin uninstall specode@pluginhub
claude plugin uninstall task-swarm@pluginhub   # 若已安装
claude plugin marketplace remove pluginhub
# 可选：清理用户级配置（含旧 ~/.specode 状态）
rm -rf ~/.specode ~/.config/specode
```

### 升级

```sh
# Claude Code
claude plugin update specode@pluginhub
claude plugin marketplace update pluginhub

# CodeBuddy
codebuddy plugin update specode@pluginhub
codebuddy plugin marketplace update pluginhub
```

### 多宿主支持

每个插件都附带**四套**独立的宿主 manifest，各宿主各自安装、各自适配。skills
prose 为单一来源、宿主中立（工具名 `AskUserQuestion` / `Skill` / `Agent` /
`Task` 保留，每个 SKILL 顶部带一条「Host-tool convention」兜底说明）；
`SessionStart` hook handler 一份文件通吃所有宿主（嵌套的
`hookSpecificOutput.additionalContext` 结构被 Claude / CodeBuddy / Codex
共同接受），唯一的按宿主差异只在 manifest 的 hook 环境变量。

| 宿主 | 每插件 manifest | 根 catalog | hooks 环境变量 | 状态 |
| --- | --- | --- | --- | --- |
| Claude Code | `<plugin>/.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` | `${CLAUDE_PLUGIN_ROOT}`（`hooks/hooks.json`） | supported |
| CodeBuddy | `<plugin>/.codebuddy-plugin/plugin.json` | `.codebuddy-plugin/marketplace.json` | `${CODEBUDDY_PLUGIN_ROOT}`（`hooks/hooks.codebuddy.json`） | supported |
| Codex | `<plugin>/.codex-plugin/plugin.json` | `.agents/plugins/marketplace.json`（Codex schema：每条 `source: {source: local, path: ./plugins/<name>}` + `policy`） | `${PLUGIN_ROOT}`（`hooks/hooks.codex.json`，matcher `startup\|resume\|clear`） | schema 按官方文档改对 — 尚未真机验证 |
| Kimi | `<plugin>/.kimi-plugin/plugin.json` | `.kimi-plugin/marketplace.json`（Kimi schema：`version` `"2"` + `id`/`source`） | —（`sessionStart.skill`，无 hooks） | 仅本地 clone — 安装 + specode 触发**已验证**；`sessionStart` 自动提示未确认 |

Codex 与 Kimi 已接线但**尚未在真机宿主上验证**。待实测清单：

- **Codex**——与 Kimi 不同，Codex **支持 monorepo 子目录安装**：
  `codex plugin marketplace add qxbyte/pluginhub` 后 `codex plugin add <name>@pluginhub`，
  由 `.agents/plugins/marketplace.json` 驱动（每条 `source: {source: "local", path: "./plugins/<name>"}`）。
  `.codex-plugin/plugin.json`（`skills: "./skills/"` + `hooks`）与 `${PLUGIN_ROOT}` 的
  SessionStart hook（`CLAUDE_PLUGIN_ROOT` 别名也认）都符合 Codex 官方文档——但整套流程
  **尚未在真机 Codex 上跑过**。
- **Kimi**——**裸仓库 URL 无法安装 monorepo 子目录插件**（据 Kimi Code 官方文档 +
  源码确认：不支持子路径 GitHub 安装、也不做多子目录扫描）。故 pluginhub 在 Kimi 上
  **仅支持本地 clone**：clone 后 `/plugins marketplace <abs>/.kimi-plugin/marketplace.json`
  （其 `source` 解析到各插件子目录），或 `/plugins install <abs>/plugins/<name>`。远程
  一键安装的后续方案是每插件 release zip（Kimi 接受 zip-URL 作为 source）。**Kimi 的
  SessionStart 由清单的 `sessionStart.skill` 承接**——specode/ragkit 在会话启动时加载
  `using-specode` / `using-ragkit`（bootstrap advisory 技能）；另两个插件无会话提示
  （skills 靠 Kimi 原生扫描发现）。端到端流程**尚未在真机 Kimi 上验证**。
- skill 里使用的 base-directory 相对路径 `../../scripts/run.sh` 在 Codex / Kimi
  的可达性未验证。
- specode 跨 skill「按名调用」（`Skill` 工具）在 Codex / Kimi 无已验证的等价机制。
- Codex 的 `ask_user_question` 仅 Plan mode 可用，可能影响 specode 的执行方式
  selector；未验证。
- task-swarm 在 Codex 上：子代理派发是 `spawn_agent` / `wait_agent` / `close_agent`，
  且需在 `~/.codex/config.toml` 开 `multi_agent = true`；`agents/*.md` 是 Claude/CodeBuddy
  agent 格式，Codex **不加载**，故按角色的工具隔离（reviewer/validator 无 Edit/Write）
  靠 prompt 约束、不是工具层强制。这已写进 swarm SKILL 的 Host-tool convention；未在真机验证。

## 使用

specode 共有五条命令。

### 1. 新建规格

```sh
/specode:spec <需求>
```

先 `cd` 到你的项目目录——specode 以 cwd 推导项目根默认值（`git rev-parse --show-toplevel`，无 git 则 cwd），并在每条 spec 开始时让你确认一次。**首次运行**时还会询问一次文档管理目录并记住它。之后代理依次走完流水线：

1. **需求阶段** — 由 `specode:intake` skill（specode 自己的，永远走它）执行：项目分析（agent-docs 扫描 + 经验检索 + 读定位到的真实代码）→ 基于分析的澄清 → 写 `requirements.md`（含 `spec_id` / `created_at` / `project_root` frontmatter 契约）。这里也是 **ragkit / 经验检索的主节点**。
2. **设计阶段** — 生成传统设计文档 `design.md`（架构 / 模块划分 / 接口设计 / 数据流 / 错误处理 / 测试策略），通过 `superpowers:brainstorming`（只产 design）或原生撰写。
3. **计划阶段（tasks）** — 生成可执行计划 `tasks.md`（通过 `superpowers:writing-plans`，或原生任务分解）。引擎中立：所有执行路径消费同一份文件。
4. **执行方式选择器** — 从自适应 4 个选项中选择执行路径（详见上方亮点）。
5. **执行阶段** — 以 TDD 方式跑完计划，追加写入 `implementation-log.md`。
6. **验收阶段** — 对照 `requirements.md` 的 `AC-N`、`design.md` 测试策略和 `tasks.md` 勾选进度检查，然后由你确认接受。

所有输出以 4 份固定文档落在 `<specsRoot>/<slug>/` 下。

### 2. 续接规格

```sh
/specode:continue <slug>
```

`<slug>` 为必填。specode 定位到 `<specsRoot>/<slug>/`，根据已存在的文档（以及 `tasks.md` 中的 `- [ ]` 进度；5.x 存量 spec 看 `design.md`）推断当前阶段，**汇报进度简报后停下等待**——你说"继续"才续跑，也可以先补充需求变更。绝不自动续跑。不知道 slug？用 `/specode:list` 查找。

### 3. 运行执行尾段

```sh
/specode:execute <slug>
```

随时运行（或续跑）一条 spec 的执行尾段：呈现「执行方式」selector（task-swarm / superpowers / specode 自执行）→ 按选择调度引擎 → 验收。spec 管道与 `/specode:continue` 在 `tasks.md` 就绪后自动汇入此 skill；会话中断后也可手动触发。要求 `tasks.md`（或 5.x 存量 `design.md` 计划）已存在——它自己绝不生成计划。

### 4. 列出规格

```sh
/specode:list
```

列出 `<specsRoot>` 下所有规格及其推断阶段，仅供概览，不会自动续接。

### 5. 沉淀知识（流水线外）

```sh
/specode:distill <slug> [--target-dir <abs-path>]
```

手动把一个已完成的 spec（加当前 agent 上下文）提炼成**原子 case / navigation 知识点**，落到该 spec 所属项目自己的 `<project_root>/knowledge-base/`（`cases/` + `navigation/` + `MEMORY.md` 索引，gitignored），可选复制一份到 Obsidian 目录。requirements / design 阶段之后会把这些点当作**定位指针（非事实）**检索——真实代码始终是唯一事实来源。绝不自动运行；验收收尾只做提示。

## 项目结构

```
.claude-plugin/marketplace.json   marketplace 清单（specode + task-swarm + obsidian-wiki）
plugins/specode/
  .claude-plugin/plugin.json      插件清单
  hooks/hooks.json                1 个提醒式 SessionStart hook
  scripts/
    resolve_root.py               specsRoot / project_root / defaults 业务 CLI
    knowledge.py                  knowledge-base 索引 CLI（MEMORY 重建/校验/copy-to）
    spec_hooks.py                 SessionStart 规范注入
    run.sh / run.cmd              python3 → python → py 解释器探测
  skills/spec/                    /specode:spec —— 编排外壳（pipeline 引擎 + 新建入口）
    SKILL.md                      requirements → design → tasks → 交棒 execute
    references/
      selectors.md                首次目录设置问句
      obsidian.md                 specsRoot 路径解析 + 惯例
      superpowers-wiring.md       阶段 ↔ superpowers 技能映射
      retrieval.md                经验检索规格（intake 为主节点）
      knowledge-flow.md           一页纸知识流心智模型
  skills/continue/                /specode:continue <slug> —— load-and-stop + 文档即状态推断
  skills/execute/                 /specode:execute <slug> —— 执行尾段（selector → 调度 → 验收），spec/continue 亦汇入此处
    references/selectors.md       执行方式选择器逐字示例
  skills/list/                    /specode:list —— 列出各 spec 及推断阶段
  skills/intake/
    SKILL.md                      需求阶段引擎（项目分析 + 澄清 + 写需求）
  skills/distill/                 /specode:distill —— user-invocable skill（无 command），流水线外
    SKILL.md                      knowledge-base 沉淀器（case/navigation 知识点）
    references/                   拆分启发式 + 文档模板
  assets/templates/               requirements.md / design.md / tasks.md /
                                  implementation-log.md 种子模板
  tests/                          hermetic pytest 测试套件（resolve_root.py + knowledge.py）
```

配套的 **task-swarm** 插件（`plugins/task-swarm/`）是独立的多代理编排器，specode 可选择性地将执行阶段交由它负责；详见其自身的 `skills/swarm/SKILL.md` 与 `CHANGELOG.md`。**obsidian-wiki** 插件（`plugins/obsidian-wiki/`）自成一体，文档见其 `README.md` / `AGENTS.md`。

## 贡献

参见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)，其中涵盖：runtime 仅限标准库、`run.sh` CLI 调用契约、提醒式 hook 规则、hermetic 测试规范以及发版流程。

## 许可证

MIT
