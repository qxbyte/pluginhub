---
description: Use when specode needs the first-time directory setup question — verbatim AskUserQuestion example asked once when config has no specsRoot. The 执行方式 selector example moved to the execute skill in 6.3.0.
---

# First-time directory setup (asked once when config has no specsRoot, or when it's unreachable)

Trigger this when `resolve_root.py get-root` exits **3** (no config) **or 4** (configured but **unreachable** — external drive not mounted / path moved or deleted). In both cases the script cannot hand back a usable root, so the model must not proceed with a phantom path — call `AskUserQuestion` to ask the user for their document management directory, then `resolve_root.py set-root --root <abs>` to write it to `~/.config/specode/config.json`.

For exit **4** specifically, first tell the user the configured path is unreachable and why (the stderr already names it, e.g. `外置盘未挂载 /Volumes/External HD`); let them **remount and retry** (no config change) or provide a **new** absolute path (→ `set-root`). Don't silently overwrite a valid-but-temporarily-unmounted config. Example prompt:

- question: "specode 还没设文档管理目录。spec 文档要落到哪个目录？（请给绝对路径，将原样作为 specs 根，每个 spec 建 <目录>/<slug>/ 子目录）"
- header: "文档目录"
- multiSelect: false
- options:
  - label: "我来输入绝对路径"
    description: "用 Other 输入一个绝对路径（如 /Volumes/External HD/Obsidian/Notes/spec-in/<os>-<user>/specs）。"

Once the user provides the path: `resolve_root.py set-root --root <user-provided-absolute-path>` persists it → all subsequent sessions read from config and will not ask again. The user may also provide the path directly in chat; handle that equivalently.

## Non-fixed selectors (informational — no examples here)

- **执行方式 selector**: lives in the execute skill — `../../execute/references/selectors.md` (moved there in 6.3.0; the spec pipeline reaches it by invoking `specode:execute`).
- **continue requires a slug**: `/specode:continue` does not perform dynamic slug selection; use `/specode:list` to find slugs.
