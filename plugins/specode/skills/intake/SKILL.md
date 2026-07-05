---
name: intake
user-invocable: false
description: specode 的需求 intake 引擎——项目分析 + 定位 + 澄清 + 写 requirements.md。在 spec 起始阶段（requirements phase）由 specode 编排 SKILL 通过 Skill 工具按名调用（specode:intake），取代旧的「brainstorming 兼职写需求 / 或薄弱 native 问卷」。产出 <specsRoot>/<slug>/requirements.md（含 project_root frontmatter 契约）+ 交给 design 阶段的定位指针。不是用户直接触发的命令。
---

# intake — specode 需求 intake 引擎

## §0 你是谁 / 何时被调用

- specode 编排壳在 **requirements phase** 通过 `Skill` 工具按名调用你（`specode:intake`）；此时 `<specsRoot>` 已解析、`<specsRoot>/<slug>/` 目录已建、slug 已定。
- 你是 requirements 的**唯一生产者**——specode 不再分「superpowers 在/不在」两条 requirements 路径。superpowers 的 `brainstorming` 从此**只做 design**（产 design.md），不再兼职写需求。
- 你相对旧「native 2-4 问问卷」的价值全在 **§3 项目分析** + **§4 基于分析的澄清**：先读真实项目建立事实基线，再问有依据的问题——这才是 specode 版的"驱动生成能力"，不是空泛问卷。
- 你的产物：
  1. `<specsRoot>/<slug>/requirements.md`（散文需求 + 硬 frontmatter 契约，见 §1）；
  2. 一段交给 design 阶段的「**参考定位（非事实来源）**」定位指针（§5，临时上下文，不持久化为事实）。

## §1 硬约束 🔒（绝不可动）

1. **frontmatter 契约（最高优先级，用户明确要求保留）**：`requirements.md` 顶部 YAML **必须**含三个字段——`spec_id` / `created_at` / `project_root`。其中 **`project_root` 是下游 distill / task-swarm / retrieval 的单一事实源**，**只能**经 `resolve_root.py write-project-root` 单一验证写入口落盘（它校验绝对路径 / 目录存在 / `/Volumes` 挂载），**绝不手写该字段**。你换的是"谁生成 requirements 的正文内容"，**绝不破坏这套契约元素**。
2. **散文需求**：`requirements.md` 是自然语言 spec（背景 / 范围 in-out / `- [ ] AC-N` / 开放问题），**无形式化子句、无 checkbox**——计划在 tasks.md、设计在 design.md，别越界。Bug 修复用 Current / Expected 散文写在这里，不单独建 `bugfix.md`。
3. **用户可见输出中文**；技术名 / 路径 / 代码标识符 / frontmatter 键名保持英文原样。
4. **不回贴全文**（见 §6 报告纪律）。

## §2 run.sh resolver 前缀（每次 CLI 调用）

所有 `resolve_root.py` 调用**必须**走 `run.sh` 包装器 + 绝对 plugin-root。skill 驱动的 Bash 里 `$CLAUDE_PLUGIN_ROOT` 不一定有值，必须 `find` 兜底。shell 状态不跨 Bash 调用保留，所以**每次**都带这段自包含 resolver 前缀：

```bash
R="${CLAUDE_PLUGIN_ROOT:-$CODEBUDDY_PLUGIN_ROOT}"; [ -f "$R/scripts/run.sh" ] || R="$(find "$HOME/.claude/plugins/cache" "$HOME/.codebuddy/plugins/cache" -path '*/specode/*/scripts/run.sh' 2>/dev/null | sort -V | tail -1)"; R="${R%/scripts/run.sh}"
sh "$R/scripts/run.sh" "$R/scripts/resolve_root.py" <verb> <args...>
```

## §3 autonomous-mode 感知（每个 AskUserQuestion 站点适用）

本 skill 有两处会 `AskUserQuestion`（§Step1 project_root 确认、§Step3 澄清）。每处**先**按 autonomous-mode 规则判定是否跳过——完整规则（gate→key→env mapping + 决策伪代码）见 `skills/specode/references/autonomous-mode.md`。要点：`interactive == false` 且该 gate 的 key `source ∈ {env, file}` 时跳过提问用 default，否则原样 `AskUserQuestion`。本 skill 的两处 gate：project_root 确认 → key `project_root_default`；澄清 → 无独立 key，仅受 `interactive` 主开关约束（非交互则基于已有信息尽力起草、把不确定项写进「开放问题」而非阻塞）。

## §4 流程（5 步，质量在 Step 2–3）

### Step 1 — project_root 确认（必做，autonomous-aware）

1. 取默认：`resolve_root.py resolve-project-root`（返回 cwd 的 `git rev-parse --show-toplevel`，无 git 则 cwd）。
2. 按 §3 决定：`AskUserQuestion` 一次（默认值预选，让用户确认或覆盖）/ 或 autonomous 直接用 default。
3. **持有确认的绝对路径**——Step 2（约束扫描 + 检索）用它、Step 4 经 `write-project-root` 落盘。此刻 requirements.md frontmatter 尚未写，直接用持有的绝对路径，**不要** `read-project-root`。

### Step 2 — 项目分析（intake 高于问卷的关键，先读真实项目再问）

不是"问用户要什么"就完事——**先读真实项目建立事实基线**：

- **a. 项目级约束扫描**（filesystem-only）：扫下列存在的文件并以 **path-only**（不拷内容）注入 requirements 草稿的 `## 项目级约束（CLAUDE.md / AGENT.md）` 段。扫描序（去重、仅存在的）：(1) `<project_root>/CLAUDE.md|AGENTS.md|AGENT.md|CODEBUDDY.md`；(2) `<project_root>` 直接父目录下同 4 文件（覆盖 monorepo workspace 根）；(3) 用户描述中点名的子目录。段模板：

  ```markdown
  ## 项目级约束（CLAUDE.md / AGENT.md）

  > 主 agent 的 system prompt 已自动加载下列文件；这里列出来是为了 design / 执行阶段 / 下游 task-swarm subagent 都能看见这条约束链路。**优先级高于本 spec 的其他描述**：冲突时以下列文件为准。

  - `<abs/path/to/CLAUDE.md>`
  - `<abs/path/to/parent/AGENTS.md>`
  ```

  为何 path-only：主 agent 上下文已有完整内容，复制一遍只是冗余 + 陈旧风险；task-swarm 渲染 task.md 时按同样规则把路径塞进 subagent prompt。一个文件都没扫到（典型 fresh 项目）→ **整段省略**（不写「无」之类占位）。

- **b. 经验检索定位**（`<project_root>/knowledge-base/MEMORY.md` 存在时）——**这是 ragkit / 经验检索的主节点**。按 `skills/specode/references/retrieval.md` 跑：先试 Tier-0 Gate（`ragkit:query` 可用且 `knowledge-base/.ragkit/chunks.json` 存在时多路召回），否则两级 gated（Tier-1 读 MEMORY 小索引比对当前需求页面/字段/域，命中才 Tier-2 读 ≤5 点全文）。产出「**参考定位（非事实来源）**」指针（文件路径 + 调用链）。`MEMORY.md` 不存在 → **静默跳过**（不报错、不写空段）。**顶层不变量**：指针只定位真实代码，**真实代码是唯一事实**；不把 KB 内容当当前代码的真相。

- **c. 读真实代码**：对 b 定位到的关键文件**实际打开读**（不只拿路径）——理解现有结构 / 命名 / 模式，作为需求分析与范围界定的事实基线。

- **d. fresh 项目**（无 knowledge-base、无 agent docs）→ b/c 静默跳过，靠 Step 3 澄清 + 用户描述建立理解。

### Step 3 — 澄清（brainstorming 级，非固定问卷）

在 Step 2 的项目分析之上做**逐条澄清**（一次一个问题、优先多选），围绕 **purpose / scope（in / out）/ constraints / success criteria**。关键：**由 Step 2 的分析驱动**——问的是「基于现有的 `X` 代码/模式，这个需求该怎样接入 / 边界在哪」这类**有依据的问题**，不是空泛问卷。

- autonomous-aware（§3）：非交互则基于已有信息尽力起草，把不确定项写进「开放问题」，不阻塞。
- **何时停**：intent / scope / AC 足够清晰、开放问题已列出即可——不要过度追问（YAGNI）。

### Step 4 — 写 requirements.md

按 `assets/templates/requirements.md` 结构写正文：`## 背景 / 为什么` · `## 范围`（包含 / 不包含）· `## 验收标准`（`- [ ] AC-N`，可观察可验证）· `## 开放问题`（+ Step 2a 的 `## 项目级约束` 段，若有）。落 `<specsRoot>/<slug>/requirements.md`。

然后落 **frontmatter（§1 硬约束）**：

1. 写 `spec_id: <slug>` / `created_at: YYYY-MM-DD`（可随正文一起写进顶部 YAML）。
2. **`project_root` 只经单一写入口落盘**：
   ```bash
   sh "$R/scripts/run.sh" "$R/scripts/resolve_root.py" write-project-root --spec <specsRoot>/<slug> --root <Step1 确认的绝对路径>
   ```
   它校验并把 `project_root` 写进 requirements.md frontmatter。**绝不手写该字段。**

### Step 5 — 交接给 design

把 Step 2b 的「参考定位（非事实来源）」指针作为**临时上下文**交回 specode 编排（供 design 阶段用：specode 调 `brainstorming` 时把这段作为 context 传入，或 native design 直接沿用）。**不持久化为 requirements.md 的事实结论**（retrieval.md 顶层不变量）。design 默认继承这些指针、仅在开辟 intake 未覆盖的新领域时才补查（design 的检索是**条件性 top-up**，非强制）。

交接后**结束本 skill**，把控制权还给 specode 编排（它接着进入 design phase）。

## §5 报告纪律

不回贴 requirements.md 全文。报告只含：文件路径（一行）+ 3-8 条要点/关键澄清 + 开放问题（若有）+ 下一步（进入 design）。唯一例外是用户明确要求看全文。

## §6 References

- `skills/specode/references/retrieval.md` — 经验检索规格（Step 2b 的引擎；intake 是其**主节点**）。
- `skills/specode/references/knowledge-flow.md` — 一页纸知识流心智模型（KB 谁产·谁读·何时的全局图）。
- `assets/templates/requirements.md` — 需求模板（Step 4 结构 + frontmatter 契约）。
- `skills/specode/references/autonomous-mode.md` — §3 判定的完整规则来源（gate→key→env + 伪代码）。
