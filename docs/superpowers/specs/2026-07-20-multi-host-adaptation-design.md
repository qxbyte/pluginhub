# pluginhub 多宿主适配设计（Claude Code / CodeBuddy / Codex / Kimi）

日期：2026-07-20。范围：全仓 4 个插件（specode / task-swarm / obsidian-wiki / ragkit）。

## 目标

1. 插件的 skills prose 不再绑定单一宿主 CLI 的工具名——描述「想要的能力 + 常见工具名举例 + 降级路径」。
2. CodeBuddy 获得独立适配层（`.codebuddy-plugin/` manifest + marketplace），不再与 Claude Code 共用一套。
3. 新增 Codex CLI 与 Kimi Code CLI 适配（manifest + hooks 输出分支 + 安装文档）。
4. 文档与版本门禁同步扩展。

## 核心原则（三层分离）

- **skills 单源**：每插件一份 `skills/`，所有宿主共享同一内容；prose 用「能力语言」书写。
- **适配层每宿主一套**：根级 marketplace + 每插件 manifest 按宿主各自独立（`.claude-plugin/` / `.codebuddy-plugin/` / `.codex-plugin/` / `.kimi-plugin/`），互不引用。
- **启动注入按宿主接线**：SessionStart hook 协议在四个宿主间同构（stdin JSON / exit code 语义），差异只在输出形态——Claude Code / CodeBuddy / Kimi 认 `hookSpecificOutput.additionalContext` JSON；Codex 把 stdout 纯文本直接作为 developer context。hook 入口脚本按宿主 env var 分支输出。

## 能力语言改写规则

| 原写法 | 新写法 |
|---|---|
| `AskUserQuestion` | AskUserQuestion or an equivalent structured-question tool；无此类工具的宿主降级为普通文本提问（中文 prose：「AskUserQuestion 或类似的结构化提问工具」） |
| via the `Skill` tool | via the host's skill-invocation mechanism (e.g. a `Skill` tool)；无此机制则直接 `Read` 目标 skill 的 SKILL.md 并照做 |
| fork a Task / `Explore` sub-agent | dispatch a subagent（宿主等价物：Agent / Task / spawn_agent…）；只读探索型 subagent 优先，宿主无 subagent 能力→当前会话顺序执行 |
| Claude Code's native Agent/subagent | the host CLI's built-in subagent capability |
| reload Claude Code | 重启宿主 CLI |
| teammates UI / spinner 细节 | 宿主的 subagent 运行状态展示（不描述具体 UI） |

豁免不改：各级 CHANGELOG 历史、obsidian-wiki 内容示例中的模型名、superpowers skills 的功能性按名调用（软依赖，非宿主绑定）、面向人类的安装文档中各宿主命令行（本来就该逐宿主写）。

## CodeBuddy 独立层

- 根 `.codebuddy-plugin/marketplace.json`（CodeBuddy 官方 schema：`name` / `owner` / `plugins[]`）。
- 每插件 `.codebuddy-plugin/plugin.json`；specode / ragkit 在其中**内联 hooks**（用 `${CODEBUDDY_PLUGIN_ROOT}`），使 `hooks/hooks.json` 回归 Claude Code 专用。CodeBuddy 识别优先级 `.codebuddy-plugin/` > `.claude-plugin/`，两目录并存互不干扰。
- skills 内容不 fork——manifest 不写 `skills` 字段即默认读同一 `skills/`。

## Codex / Kimi 适配

- 每插件 `.codex-plugin/plugin.json`（字段与 Claude 侧同构）+ `.kimi-plugin/plugin.json`（Kimi 自有字段；specode / ragkit 用 manifest 声明 hooks）。
- 根 `.agents/plugins/marketplace.json`（Codex marketplace 路径）。
- `spec_hooks.py` / `ragkit_hooks.py`：按 env var 探测宿主——`CODEBUDDY_PLUGIN_ROOT` → CodeBuddy JSON、`CLAUDE_PLUGIN_ROOT` → Claude JSON、其余（Codex 注入 `PLUGIN_ROOT`）→ 纯文本 stdout。
- **待实测**（本机未装两 CLI）：① 两平台上 skill 基目录相对路径 `../../scripts/run.sh` 的可达性；② 按名调 skill 的等价机制（specode spec→intake/execute 链路）；③ Codex `ask_user_question` 仅 Plan mode 可用的门禁对 selector 的影响；④ Kimi 对子目录多插件仓库的安装支持。README 中逐条标注。

## 文档与门禁

- `scripts/check_marketplace_versions.py`：扩展为「每插件 4 份 manifest + 根级 2 份 marketplace」锁步校验（`.agents/plugins/marketplace.json` 为 Codex 目录格式，若含 version 一并校验）。
- README（EN/zh）安装矩阵四宿主各自成节；CONTRIBUTING 增补多宿主约定；CLAUDE.md 同步（修正插件数量为 4）。
- 版本：specode 6.5.0 / task-swarm 0.12.0 / obsidian-wiki 2.2.0 / ragkit 0.2.0，CHANGELOG（中文）定版，不打 tag。
