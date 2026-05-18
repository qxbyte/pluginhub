---
name: specode
description: Specification-driven workflow driven by spec-mode discipline. All hooks are advisory injections — never blocking. Activates only when the user explicitly invokes `/specode:spec`, `/specode:continue`, `/specode:status`, `/specode:end`, `/specode:task-swarm`, or explicitly asks to use spec mode. While active, every user-facing turn must respect the phase order, selector format, code-doc sync reminders, and the status footer.
---

# specode — Spec-Mode 工作流（v0.6）

文件优先的规范驱动工作流。`requirements.md` / `bugfix.md` / `design.md` / `tasks.md` / `acceptance-checklist.md` / `implementation-log.md` 是事实源；代码改动总是滞后于文档落地。所有 hook 都是**提示式注入**，永远不阻断；当 hook 注入失败或缺失时，本 SKILL.md 的硬约束仍然完整有效。

## Activation Guard

只在以下任一情况激活：

- 用户当前输入包含 `/specode:spec`、`/specode:continue`、`/specode:status`、`/specode:end`、`/specode:task-swarm` 中任意一个。
- 用户显式说"使用 spec 模式" / "启用 spec 模式" / "用 spec 模式" / "use spec mode"。
- 当前会话的 `~/.specode/sessions/<claude_session_id>.json` 中 `mode=active` 或 `mode=readonly`（即上一个 turn 仍在 spec 模式内）。

**不要**为普通编码、随手 planning、随口提需求 / 设计 / 任务清单 / bugfix / 实现 / 文档请求激活本 skill。激活后即按 §Session Lifecycle 走完命令解析与持久会话创建。

如果 `mode=ended` 或 sessions 文件不存在，且当前输入不命中上面任一触发条件 → **不要激活**，按普通对话处理。

## Session Lifecycle

### 持久会话是唯一模式

所有 `/specode:spec <需求>` 都创建持久 spec session，**不再有 `--persist` 标志**。一次性运行已不支持；如需快速试验，写完文档后立即 `/specode:end` 即可。

`/specode:spec <需求>` 的展开：

1. 解析需求文本前缀 `<名称>：<内容>` 或 `<名称>: <内容>`（半角 `:` 必须带空格）；命中则左半部分作为显示名 / slug 来源，右半部分作为需求源文本。否则整段都是源文本，由你从内容推导 slug。
2. 推导出 ≤64 字符、小写、连字符分隔的语义英文 slug（如 `login-password-rule`、`undo-redo`、`dark-mode`）。
3. 调 `spec_init.py --name <slug> --requirement-name "<显示名>" --source-text "<需求>" --session <session_id>`。CLI 完成三层根目录解析、目录创建、`<spec-dir>/.config.json` 与 `~/.specode/sessions/<session_id>.json` 双写、active-pointer 更新。
4. CLI 返回 JSON（`spec_dir` / `specId` / `session_id` / `phase=intake`）后进入 intake 阶段。

`/specode:continue [slug]` 的展开：

1. 无 slug → 列出当前 root 下全部可恢复 spec（按 §Multi-Window + Lock 的"列表 + 用户回复编号"形式），让用户选；选完进入有 slug 分支。
2. 有 slug → 解析 `spec_dir`，调 `spec_session.py acquire --spec <dir> --session <id>`。
   - 成功（exit 0）→ 调 `spec_session.py continue --spec <dir> --session <id>`（绑定 sessions 文件 + 写 active-pointer）→ 调 `spec_session.py load --spec <dir>` 拿到 spec 状态摘要 → 输出"已加载 spec" 报告 + 状态行 footer → **end turn**。绝不开始任何任务、不评估验收。
   - LockHeld（exit 4）→ 输出锁状态摘要（持有者 session_id 前 8 位 + 最近 heartbeat 时间）→ 呈现 `takeover-options` 选择器（类型 A，详见 §Selectors）→ end turn 等待用户选 1 强制接管 / 2 只读 / 3 取消。

`/specode:end` 的展开：

1. 调 `spec_session.py end --session <id>`：CLI 释放当前会话持有的 spec 锁（写 `<spec-dir>/.config.json` lock=null）、把 `sessions/<id>.json` 写为 `{mode: "ended", ended_at: <now>, ...}`。
2. 写入失败 → exit 1，向用户报告失败，**不要假装结束**（in-memory 半成功是禁区）。
3. 成功 → 简报"spec 会话已结束（slug=<slug>）"。**从下一 turn 起 hook 看到 mode=ended 立即停止注入**，本 SKILL.md 也不再激活。

`/specode:status` 的展开：调 `spec_session.py status --session <id>` 或 `spec_status.py`，简报当前 session / spec / phase / lock / tasks 计数。只读，不触发心跳。

### session_id 的获取与传递

- `SessionStart` hook 在每次 Claude Code 会话启动时向你注入 `additionalContext`，包含本会话的 `claude_session_id` 字符串。
- `UserPromptSubmit` hook 在每轮用户提交前**重复**注入当前 `session_id`，避免你在长上下文里忘记。
- 你**调任何 specode CLI** 时必须把 `--session <session_id>` 作为参数传入。CLI 若收到的 session_id 与 sessions 文件不一致或不存在 → exit 1，并提示你重读最近的 hook 注入。
- 永远**不要**自己 invent session_id；永远不从用户输入解析 session_id；永远不在 chat 里 echo 完整 session_id 给用户（状态行 footer 只取前 8 位）。

### 强制双写语义

`/specode:spec` / `/specode:continue` / `/specode:end` 的任何写操作都要同时写 `<spec-dir>/.config.json` + `~/.specode/sessions/<session_id>.json`，由 CLI 用 tempfile + `os.replace()` + `os.fsync()` 保证原子性。**任一写失败 → CLI 整体 exit 1 + 回滚已变更字段**，你在 chat 里如实报告失败原因，不要把 in-memory 状态当成已落地。

## Status Footer

active spec 期间，**每一次响应末尾**必须额外输出一行状态行 footer，与正文之间空一行。模板：

```text
─── spec-mode ─── spec: <slug> | session: <session_id 前 8 位> | phase: <phase> | /specode:end 退出
```

只读模式追加 `[只读]` 字段：

```text
─── spec-mode ─── spec: <slug> | session: <session_id 前 8 位> | phase: <phase> | [只读] | /specode:end 退出
```

约束：

- 状态行是**机器友好格式**：用 `─── spec-mode ───` 三符号包裹，不允许换成其他装饰、不允许加 emoji。
- session 字段只显示 session_id 前 8 位（够用且可读）。
- 当本 turn 输出 selector 时，状态行放在 selector **之前**一行，再空一行接 selector；`AWAITING_USER_CHOICE` sentinel 仍是 selector 段的最后一行。
- `mode=ended` / 不在 spec 模式 → **不**输出状态行（避免误导用户以为还在 spec 模式）。
- 缺失状态行视作流程违规——hook 不会因此阻断，但用户与下一轮 turn 都会察觉。

## Selectors

每个 phase-gate 节点必须输出**结构化的选择器文本**，由用户选编号后才能推进下一步。永远不要把选择器写成自由叙述（"你可以选 A 或者继续聊聊"）。

### 三种类型

- **类型 A 单列单选（single-select）**：一个问题、互斥选项、单选。绝大多数 phase-gate 用 A。
- **类型 B 多项串行决策（wizard）**：一组**无依赖**的子问题打包在一个 wizard 里，每个子问题独立编号，用户一次性回复全部。**仅用于 intake 阶段的"需求澄清问答"**——为了避免来回 5 轮 turn 把一组澄清点问完。
- **类型 C 复选框多选（multi-select）**：非互斥选项可同时勾选。**v0.6 仅 iteration-scope 一个场景占位**，其他场景不要用 C。

三种类型的完整文本骨架见 `references/prompts.md`。下面只列共同铁规：

- 必须以 `AWAITING_USER_CHOICE` 单独一行**结尾**——这是 turn 终止 sentinel；输出后立即 end turn。
- 每个选项带编号 + 标签 + 一行说明；类型 A / C 末尾固定两个保留位 `Type something` + `Chat about this`；类型 B 每个决策点末项 `Type something`、wizard 整体末段加 `Chat about this`。
- 类型 A 至多 1 个 `（推荐）` 标记；无强推荐时全部不带。
- 选项个数：类型 A 2–5 / 类型 B 决策点 2–5、每个决策点 2–4 项 / 类型 C 2–6。

### 8 个固定场景

下表给出 (场景 key → 类型 → 触发 phase → 标题) 的固定映射；详细选项标签、推荐项、文本骨架与 hook 注入提示见 `references/prompts.md` §场景常量库。

| 场景 key | 类型 | 触发 phase | 标题 |
|---|---|---|---|
| `workflow-choice` | A | 进入 requirements 前 | 工作流选择 |
| `clarification-wizard` | B | intake，写需求前 | 需求澄清（共 N 个决策点） |
| `clarification-done` | A | intake 澄清结束 | 需求澄清是否完成？ |
| `doc-confirm-requirements` | A | requirements.md 生成后 | requirements.md 文档确认 |
| `doc-confirm-bugfix` | A | bugfix.md 生成后 | bugfix.md 文档确认 |
| `doc-confirm-design` | A | design.md 生成后 | design.md 文档确认 |
| `doc-confirm-tasks` | A | tasks.md 生成后 | tasks.md 文档确认 |
| `tasks-execution` | A | tasks.md 确认后 | 任务执行选择 |
| `takeover-options` | A | `/specode:continue` 命中 LockHeld | 该 spec 已被其他窗口持有 |
| `acceptance-gate` | A | acceptance 完成 | 验收结论 |
| `iteration-scope` | C | iteration 子循环开始（v0.7 启用，v0.6 占位） | 本轮 iteration 调整范围 |

### 看到 hook 注入"必须呈现 X 选择器"提示时的硬约束

`UserPromptSubmit` hook 在 phase-gate 节点会向你注入形如 `## ⛔ 必须呈现「<场景中文名>」选择器（类型 ?）` 的提示。看到该提示时：

- 当前 turn **唯一**正确动作 = 按对应类型骨架输出该 selector + 状态行 footer + `AWAITING_USER_CHOICE` end turn。
- 不允许把 selector 拆成两轮、不允许"先回答用户上一句再 selector"、不允许跳过 selector 直接做下一步操作。
- 类型与场景的映射**固定**（见上表）—— 不允许"我觉得这里改用类型 C 更好"自行变换。
- 没看到该提示但你自己判断到了 phase-gate（如 hook 失败 / 上下文里没看到 hook 文本）→ 按上表查类型并按骨架输出，不要因为"没人催"就跳过。
- 保留位**必须留**：类型 A 末尾 `Type something` + `Chat about this`；类型 B 每决策点末项 `Type something` + wizard 整体末段 `Chat about this`；类型 C 末尾 `Type something` + 回复格式中的 `none` / `Chat about this`。

→ 三种类型完整骨架、8 个场景的选项标签与推荐项详见 `references/prompts.md`。

## Code-Doc Sync Reminders

### Spec 文档清单（6 份）

| 文档名 | 用途 | 何时该更新 |
|---|---|---|
| `requirements.md` | 需求-first 工作流的需求文档（EARS SHALL 写法） | 需求 / 验收标准调整 |
| `bugfix.md` | bugfix 工作流的问题描述（与 requirements.md 互斥） | 缺陷范围 / 复现步骤 / 期望行为调整 |
| `design.md` | 技术设计（架构 / 接口 / 数据模型） | 架构 / 接口 / 数据模型决策调整 |
| `tasks.md` | 任务拆分 + 进度 + `_需求：x.y_` traceability | 任务范围调整 / 状态推进 `[ ]` → `[~]` → `[x]` |
| `acceptance-checklist.md` | 验收检查表（跟随 requirements / bugfix） | requirements / bugfix 改动后**同 turn** 重写 |
| `implementation-log.md` | 实现记录（可选） | 实施期间记录设计偏离、解决方案、关键决策 |

→ 6 份文档的章节模板与 EARS SHALL 写法详见 `references/templates.md`。

### Document-first 纪律（响应约束）

每轮收到用户输入时，先评估是否触发文档变更：

1. **看到「📝 文档优先提醒（输入侧）」** + 用户输入含需求 / 设计 / 任务 / 验收调整 → 本 turn **优先 Edit 对应文档**，**再**处理代码或解释。
2. **看到「🔄 代码-文档同步提醒（输出侧）」** + 本 turn 触碰过 Write/Edit 源码 → turn 结束前补齐对应文档；若实在无法当 turn 补齐，在 chat 里**显式承诺**"下一轮第一件事是补齐 X 文档"，并在下一轮立刻做到。
3. **没看到提醒**（hook 失败 / 无 active spec）→ 仍保持 document-first 纪律。这是 SKILL.md 的硬约束，不依赖 hook 触发。
4. `acceptance-checklist.md` **跟随式重写**：requirements.md / bugfix.md 一旦改动，必须在**同一轮 turn 内**重写 acceptance-checklist.md，没有单独的"确认门"。详见 `references/workflow.md` §acceptance-checklist 跟随式生成。
5. `implementation-log.md` 是"轻量级补救手段"：如果实在没法 turn 内重写 design.md / tasks.md，至少在 log 里追加一行（≥30 字），为下一会话留线索。空 log 等于没改过。

### 提醒不阻断 = 你自担风险

所有 hook 注入提醒永远 `exit 0`、永远不阻断工具调用。你可以选择无视提醒，但代价是：

- **未写入文档的 chat 承诺在 `/specode:end` / `SessionEnd` 后全部丢失**。下一次 `/specode:continue` 时只能看到落盘文件——chat 内容不在事实源里。
- `spec_lint.py` 会在 `acceptance-checklist.mtime < requirements.mtime` 时报 WARNING；`tasks.md` 里没有 `_需求：x.y_` traceability 的任务也会报 WARNING。WARNING 只是提示，不强制阻断，但是用户可见。
- 下一轮 hook 仍会注入提醒，错位不会自动愈合。

## Help Fast-path

当用户输入命中 `/specode:spec -h` 或 `/specode:spec --help`（容忍前后空白）：

- `UserPromptSubmit` hook 会注入一段 `## ⛔ /specode:spec -h fast-path` 提示，里面包含**完整帮助文本**（由 hook 进程从内置常量或 plugin 自带的 `references/help-output.md` 读取）。
- 本 turn **唯一动作** = 把帮助文本**逐字**用 \`\`\`text 围栏包裹后输出，立即 end turn。
- 禁止任何额外修辞（"以下是帮助" / "希望对你有帮助" / "请告诉我您要做什么" 都不允许）。
- 禁止自己改写帮助文本、禁止省略其中任何行、禁止改大小写。
- `/specode:spec --vault-status` / `/specode:spec --detect-vault` / `/specode:spec --sync-status` 走同样的 fast-path：hook 直接执行对应 CLI（`spec_vault.py status` 等），把 stdout 包成 `additionalContext` 让你 verbatim 打印。

如果没看到 hook 注入的 fast-path 文本（hook 失败 / 旧版本 / 全局 bypass `SPECODE_GUARD=off`），仍按一般原则简短回答"请运行 `python3 plugins/specode/scripts/spec_vault.py status` 查询"——绝不自创"帮助内容"。

## Workflow Selection

进入 requirements 前必须先呈现 `workflow-choice` 选择器（类型 A）让用户挑工作流类型：

| 选项 | 适用场景 |
|---|---|
| **Requirements first** | 行为优先的新特性：先把 EARS SHALL 写清楚，再补技术设计。**默认推荐**。 |
| **Technical Design first** | 架构约束已知的新特性：先把 design.md 框架定下来，再反推 requirements。 |
| **Bugfix** | 缺陷修复 / 回归测试：用 `bugfix.md`（Current / Expected / Unchanged）替代 `requirements.md`。 |

工作流一旦确认，本 spec 的 `<spec-dir>/.config.json.workflow` 字段记录为 `requirements` / `design` / `bugfix`。后续 phase 序列按选定的工作流走（详见 `references/workflow.md`）。

不要在选 workflow 之前生成任何 spec 文档；不要凭印象把 workflow 设为某个默认值——必须用 selector 让用户主动选。

## Phase Order

```
intake → requirements / bugfix → design → tasks → implementation → acceptance → iteration
```

Phase 与可写文档、可执行操作对照：

| Phase | 可写文档 | 允许 Edit 源码？ | 主要操作 |
|---|---|---|---|
| `intake` | （无） | 否 | 解析需求 / 必要时 `clarification-wizard` / `workflow-choice` |
| `requirements` 或 `bugfix` | `requirements.md` 或 `bugfix.md` + `acceptance-checklist.md`（同 turn） | 否 | `spec-writer` agent 生成文档；`doc-confirm-*` 选择器 |
| `design` | `design.md` | 否 | spec-writer 生成；`doc-confirm-design` |
| `tasks` | `tasks.md`（必须含 `_需求：x.y_` traceability） | 否 | spec-writer 生成；`doc-confirm-tasks` → `tasks-execution` |
| `implementation` | `tasks.md`（推进 checkbox 状态）+ `implementation-log.md`（追加） + 源码 | **是** | 按 tasks.md 任务顺序写代码 + 跑测试 + 推进 `[ ]` → `[~]` → `[x]` |
| `acceptance` | `acceptance-checklist.md`（填实际结果与结论列） | 不允许新功能改动；允许回退 / 测试修复 | 跑验收命令，逐行填 acceptance-checklist.md；最终 `acceptance-gate` |
| `iteration` | 全部可写 | 是 | iteration 子循环（详见 `references/iteration.md`） |

phase 切换永远走 `spec_session.py phase-transition --spec <dir> --session <id> --from <p> --to <p>` —— CLI 同步写 `<spec-dir>/.config.json` + `sessions/<id>.json`，原子写、失败回滚。**不要**手动改 `.config.json` 里的 `currentPhase` 字段。

→ 详见 `references/workflow.md`（三档工作流的 phase 子步骤、phase-gate 输出顺序、`/specode:continue` 接管流程）。

## Document Root Resolution

`<doc-root>` 解析顺序（与 `spec_init.py:resolve_document_root` / `spec_vault.py resolve_spec_root` 一致）：

1. **命令行 `--root <path>`** 或环境变量 `SPECODE_ROOT`。
2. **`~/.config/specode/config.json` 的 `obsidianRoot`**（或类 unix 下 `$XDG_CONFIG_HOME/specode/config.json`）。
3. **自动检测 Obsidian vault**：按平台读 `obsidian.json` → 过滤路径不存在的 vault → 优先选 `open=true` 且 timestamp 最新的；多 vault 时让用户在 chat 里回复编号。

三层全 miss → **硬停 + 引导**：

```text
未找到 specode 文档根目录。请用以下任一方式设置：

1. 临时指定（仅本次）：
     /specode:spec --root /path/to/dir <需求>

2. 永久绑定 Obsidian vault：
     /specode:spec --set-vault /path/to/vault

3. 永久绑定自定义根目录：
     /specode:spec --set-root /path/to/dir

设置后再次运行 /specode:spec <需求>。
```

**不要发明 fallback**（不要默认到 cwd / `~/specs` / 项目目录）—— 这条规则继承自 spec-mode，避免静默把 spec 散布在到处。

vault 内的 spec 目录约定：`<vault>/spec-in/<os>-<user>/specs/<slug>/`，其中 `<os>-<user>` 由 CLI 按当前平台与用户名计算（如 `macos-alice`、`windows-bob`）。

→ 三平台 `obsidian.json` 路径、vault 选择规则、`spec_vault.py` 命令参考详见 `references/obsidian.md`。

## Multi-Window + Lock

锁存放在每个 spec 自己的 `<spec-dir>/.config.json.lock` 字段（不放在 `.active-specode.json` 上），**持有者键 = `claude_session_id`**。同一 spec 同一时刻只允许一个 session 写入；多窗口可同时开**不同** spec。

锁状态机 4 个状态：

- `ok` — 当前会话持锁，可写。
- `readonly` — 当前会话只读（不持锁），任何 Edit/Write 在 SKILL.md 层面被劝阻。
- `evicted` — 当前会话被其他窗口强制接管驱逐；下一次写前 `verify-lock` 返回 `evicted` → 立即转入只读 + 通知用户。
- `not_held / stale_lock` — 锁字段为 null 或心跳超过 30 分钟 → 下一次 `acquire` 静默接管。

5 个核心命令 → 详见 `references/lock-protocol.md`：`acquire` / `release` / `heartbeat` / `verify-lock` / `phase-transition`。

### 写前三重校验（铁律）

任何 spec 文档写入前必须确认：

1. **specId 校验**：active-pointer 里的 `specId == <spec-dir>/.config.json.specId`。
2. **边界校验**：`<spec-dir>` 物理位于 `<doc-root>` 之下。
3. **锁校验**：`spec_session.py verify-lock` 返回 `ok`。

任一失败 → **拒绝写入**，向用户报告原因；不要静默继续。

### 心跳触发点

- **每次写 spec 文档前**调一次 `spec_session.py heartbeat --spec <dir> --session <id>`。
- **每次回答用户消息前**如果距上次心跳超过 5 分钟，也调一次。
- 只读命令（`load --json` / `status` / `read-session` / `spec_lint.py` / `spec_status.py`）**不**触发心跳。
- v0.8 起 `UserPromptSubmit` 的 `on-heartbeat-quiet` hook 会自动静默续约——你不需要手动调用；但 v0.6 / v0.7 仍由你显式触发。

### 多窗口接管三选项

`/specode:continue <slug>` 命中 LockHeld（exit 4）时：

1. 你先输出锁状态摘要：`持有者 session_id 前 8 位 + 最近 heartbeat 时间`。
2. 呈现 `takeover-options` 选择器（类型 A），选项**逐字使用**：`1. 强制接管` / `2. 只读查看` / `3. 取消` + 保留位。无推荐项（让用户判断对方是否仍活跃）。
3. End turn 等用户选。
   - 选 1 → 调 `spec_session.py acquire --spec <dir> --session <id> --force`，告知用户对方下一次写操作会被 `verify-lock` 拒绝。
   - 选 2 → **不**调 acquire，调 `spec_session.py load`，写 `sessions/<id>.json.mode=readonly`；后续所有 Edit/Write 在 SKILL.md 层面拒绝，状态行 footer 加 `[只读]`。
   - 选 3 → 不做任何写动作，回到对话起点。
4. 被驱逐窗口的下一次 `verify-lock` 返回 `evicted` → SKILL.md 引导该窗口转为只读 + 告知用户"你的会话已被 session `<newId 前 8 位>` 强制接管。当前 spec 在此窗口已转为只读。继续工作请用 `/specode:continue <slug>` 选择强制接管回来。"

→ 锁字段 schema、stale 阈值、被驱逐窗口完整行为、原子性保证详见 `references/lock-protocol.md`。

## Pre-requirements Clarification (Plan-mode)

如果用户的 `/specode:spec <需求>` 输入存在影响 scope / behavior / UX / data / validation / acceptance 的真实歧义：

- 留在 `intake` phase，**不要**先写 `requirements.md` / `bugfix.md`。
- 不要凭空 invent 缺失的细节；不要假设。
- 不要把一组澄清问题拆成多轮 turn 来回问——**一次性**通过 `clarification-wizard`（类型 B）呈现：2–5 个**无依赖**的决策点，每个 2–4 个互斥选项 + 末项 `Type something`，wizard 整体保留 `Chat about this` 逃生口。
- 子问题与选项由你结合用户输入和 `references/templates.md` 的章节结构自行生成 —— inputs 不足以构成一个决策点就不要塞进去；连一个决策点都没有（需求已足够清晰）就直接跳到 `clarification-done`，不输出 wizard。
- 用户回复后下一轮先解析回答，再呈现 `clarification-done`（类型 A），推荐选项是 `进入下一阶段`；用户选"继续澄清"再发一轮 wizard。

→ 三种类型骨架与具体场景常量见 `references/prompts.md`。

## Output Language

- 描述性内容（说明、解释、总结、状态更新、问题确认、selector 选项标签与说明、状态行 footer 之外的正文）一律**中文**。
- 技术名 / 命令 / 文件路径 / 函数名 / 变量名 / commit message / PR 标题 / 代码块内部 / 本 SKILL.md 与 references 文件名保持英文原样。
- selector 选项标签用中文动词式短语（`确认` / `查看全文` / `继续沟通` / `强制接管` / `只读查看` / `取消`），命名与 `references/prompts.md` 一致。
- 禁用口语 / 暧昧措辞（"够了" / "差不多" / "应该可以了" / "随便选" / "我猜" / "稍等"）—— 走 selector / 走 wizard / 直接给结果，三选一。

## Document Output Brevity

**写完 spec 文档后不要在 chat 里 reprint 全文**。每份文档生成 / 更新后，正文中只输出：

- 文档**绝对路径**。
- **3–8 条**变更要点（一行一条；引用章节名 / 增加的 SHALL 编号 / 新增任务编号）。
- 未决问题（如有）。
- 下一步操作建议。

之后立刻呈现对应 `doc-confirm-*` 选择器。用户主动要求"查看全文"（selector 选项 2）才完整 echo 文档；否则一律省略。

- 不允许把 EARS SHALL 全列在 chat。
- 不允许把 tasks.md 全部 checkbox 列在 chat。
- 不允许把 design.md 的架构图 / 接口签名完整重述在 chat。

## References

| 文件 | 用途 |
|---|---|
| `references/workflow.md` | phase 序列、三档工作流子步骤、phase-gate 输出顺序、`/specode:continue` 完整流程、`phase-transition` 命令使用 |
| `references/lock-protocol.md` | 锁状态机（持有者键 = `claude_session_id`）、5 个核心命令、stale 阈值、接管三选项、被驱逐窗口行为、写前三重校验 |
| `references/obsidian.md` | 三平台 `obsidian.json` 路径、vault 选择规则、多 vault 用户选编号、`<vault>/spec-in/<os>-<user>/specs/` 目录约定 |
| `references/prompts.md` | 选择器三种类型骨架、8 个固定场景常量库（标题 + 选项标签 + 推荐项 + 触发 phase）、Plan-mode 澄清示例 |
| `references/templates.md` | 6 份 spec 文档的章节模板、EARS 四种 SHALL 写法、`_需求：x.y_` traceability 规范 |
| `references/iteration.md` | iteration 子循环规则、文档累积写法、`/specode:end` 与再次 acceptance 通过的退出条件 |

跨文档引用一律相对路径（`references/workflow.md` 等）。

---

**最后一条铁律**：本 SKILL.md 不依赖任何前置阻断式 hook、不依赖任何"脚本输出 selector 文本"的中间层。所有规则靠 SKILL.md + references 自律 + hook 注入提醒 + CLI 确定性状态机协作执行。Hook 失败 / 全局 bypass / 上下文丢失时，本文件的硬约束仍然完整有效。
