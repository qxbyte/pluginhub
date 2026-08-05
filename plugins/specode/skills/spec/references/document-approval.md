---
description: Canonical per-document approval gate for requirements.md, design.md, and tasks.md.
---

# Fixed document approval gate

After producing and verifying one of `requirements.md`, `design.md`, or
`tasks.md`, report only its path, 3-8 summary bullets, and open questions.
Then call `AskUserQuestion` (or the nearest structured-question equivalent):

- question: "`<document>` 已生成并保存。是否确认并进入 `<next-phase>`？"
- header: "确认文档"
- options:
  - label: "确认并继续"
    description: "批准当前文档，并在下一轮进入下一阶段。"
  - label: "需要修改"
    description: "不批准；请在 Other 中填写修改意见。"

After asking, immediately end the turn and do not generate the next document in the same turn. If no structured-question tool exists, ask the same question in plain Chinese and still end the turn.

Only an explicit approval advances. Never infer approval from silence,
ambiguity, or a modification request. Apply requested changes only to the
current document, show the updated summary, and present this gate again.
