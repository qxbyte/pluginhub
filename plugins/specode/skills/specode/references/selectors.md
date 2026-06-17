---
description: Use when design 完成、需向用户呈现「执行方式」选择 —— specode lite 唯一固定 selector 的 AskUserQuestion 逐字范例。
---

# 执行方式 selector（唯一固定 selector）

design.md 确认后调 `AskUserQuestion`，**自适应组装选项**（检测装了哪个引擎才纳入对应选项，最多 4 项；都没装则只剩 specode 自执行，可直接走不必弹 selector）。逐字传 label/description（不翻译/不简化）：

- question: "design 已完成。怎么执行？"
- header: "执行方式"
- multiSelect: false
- options（按已装情况裁剪）:
  - label: "委托 task-swarm（多 agent 并发）"
    description: "需已装 task-swarm。读 design Task + Files 生成 pipeline.yml，过目后并发执行。"
  - label: "superpowers subagent-driven（每 Task 派全新 subagent + 两阶段评审，推荐）"
    description: "需已装 superpowers。调 subagent-driven-development：每 Task 派全新 subagent，Task 间两阶段评审，上下文干净。"
  - label: "superpowers executing-plans（当前会话顺序批量 + checkpoint）"
    description: "需已装 superpowers。调 executing-plans：单会话内顺序执行 + checkpoint。"
  - label: "specode 自执行（顺序单 agent）"
    description: "都没装时的降级。主代理按 design Task 直接 TDD + 自验。"

约束：调用后立即 end turn 等用户选；选定后同一 turn 内按所选路径推进（见 SKILL.md §流程）。
注：`subagent-driven-development` / `executing-plans` 是 superpowers skill（底层用 Claude Code 内置 Agent/subagent），非 Claude 内置工作流。

## 首次设置目录（config 无 specsRoot 时问一次）

`resolve_root.py get-root` 返回 exit 3（无 config）时——脚本取不到 = 模型取不到——调 `AskUserQuestion` 问用户文档管理目录，再 `resolve_root.py set-root --root <abs>` 写进 `~/.config/specode/config.json`。范例：

- question: "specode 还没设文档管理目录。spec 文档要落到哪个目录？（请给绝对路径，将原样作为 specs 根，每个 spec 建 <目录>/<slug>/ 子目录）"
- header: "文档目录"
- multiSelect: false
- options:
  - label: "我来输入绝对路径"
    description: "用 Other 输入一个绝对路径（如 /Volumes/External HD/Obsidian/Notes/spec-in/<os>-<user>/specs）。"

用户给出路径后：`resolve_root.py set-root --root <用户给的绝对路径>` 持久化 → 此后会话不再问。用户也可在 chat 直接给路径，等价处理。

## 非固定 selector（说明，不在此给范例）
- **continue 须带 slug**：`/spec continue` 不做无-slug 动态选择；查 slug 用 `/spec list`。
