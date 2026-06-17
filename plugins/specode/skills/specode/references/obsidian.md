---
description: Use when 解析 spec 文档落盘根目录、首次设置目录、或 /spec list 列 spec —— specsRoot 三层解析与目录约定。
---

# specsRoot 解析与目录约定

## 根目录来源：config 唯一存储，统一来取

specsRoot（用户的文档管理目录）**只存一处**：`~/.config/specode/config.json` 的 `specsRoot` 键。所有需要这个目录的脚本 / 命令都经 `resolve_root.py get-root` 到这里取——它是**唯一取数口**，别处不要各自读 config。

`get-root` 解析顺序：
1. `--root` flag / env `SPECODE_ROOT`（临时覆盖，power-user 用，不写盘）
2. `~/.config/specode/config.json` 的 `specsRoot`（**常态来源**，每次启用都从这里取）
3. 取不到（无 config）→ **脚本取不到 = 模型取不到** → 模型用 `AskUserQuestion` 问用户「文档管理目录」（绝对路径）→ `resolve_root.py set-root --root <abs>` 把它**直接写进上面那个 config 文件** → 此后所有会话都从 config 取，不再问。

CLI 经 run.sh：`resolve_root.py get-root` / `set-root --root P` / `list-specs`（问法范例见 `selectors.md` §首次设置目录）。

## 目录约定
- 用户提供的目录**原样**作为 specs 根，specode 不拼任何子结构（用户可直接给 `.../spec-in/<os>-<user>/specs` 这种完整路径）。
- 每个 spec = `<specsRoot>/<slug>/`，固定含 `requirements.md` / `design.md` / `implementation-log.md`。
- `pipeline.yml` 仅委托 task-swarm 时临时生成，非固定产物。
- project_root = 当前终端 cwd（不询问；约定先 cd 到项目目录再开聊）。

## 文档即状态（phase 推断）
| 目录状态 | phase |
|---|---|
| 无 requirements.md | intake |
| 有 requirements.md，无 design.md | design |
| 有 design.md，有未勾选 `- [ ]` Task | 执行中 |
| design.md Task 全勾选 | 完成 |
