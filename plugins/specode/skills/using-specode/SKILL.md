---
name: using-specode
description: Overview of the specode plugin and how to activate it — the spec-driven workflow, its five commands, and when to enter spec mode. On Kimi Code this is loaded at session start via the manifest's sessionStart.skill; on hosts with a SessionStart hook the same advisory is injected by the hook instead.
---

# using-specode — specode 可用性说明（会话启动注入）

> 本技能是 specode 的**会话启动 advisory**。它不执行任何流程，只告诉宿主 agent「specode 存在、何时用、怎么进」。在 Kimi Code 由清单的 `sessionStart.skill` 于会话开始时注入；在有 SessionStart hook 的宿主（Claude Code / CodeBuddy）由 hook 注入等价文案，无需本技能。

specode（spec-mode 轻量工作流）可用。**仅在**用户输入下列命令、或显式要求用 spec 模式时激活；否则按普通对话处理，不要主动进入 spec 流程：

- `/specode:spec <需求>` — 新建规格，走 requirements → design → tasks → 执行方式 → 执行 → 验收。
- `/specode:continue <slug>` — 续接已有规格（读固定文档、报进度后停下等指令）。
- `/specode:execute <slug>` — 随时手动承接执行尾段（执行方式 selector → 执行 → 验收）。
- `/specode:list` — 列出所有规格及其推断相位。
- `/specode:distill <slug>` — 流水线外，把完成的规格沉淀成定位型知识点。

激活后的要点：① requirements 由 `specode:intake` 技能产（项目分析 + 澄清 + 写需求）；design / tasks 各相位优先调对应 superpowers 技能，缺席则 specode-native 降级；② 4 份固定产物 `requirements.md` / `design.md` / `tasks.md` / `implementation-log.md` 永远以固定文件名落在 `<specsRoot>/<slug>/`；③ tasks 完成后由 `specode:execute` 技能承接执行尾段。

> Host-tool convention 🔧：本插件各技能中出现的工具名（`AskUserQuestion` / `Skill` / `Agent` / `Task`）在有该工具的宿主上直接照用最可靠；缺该工具的宿主用最近等价物，都没有则降级为纯文本提问 / 直接读目标 SKILL.md / 顺序单代理执行。行为语义才是要点，不是具体工具名。
