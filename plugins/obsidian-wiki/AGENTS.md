# obsidian-wiki — agent guide

维护 Obsidian **LLM-Wiki** 的一套 skill。代码通用、**零结构硬编码**：每个库的结构配置存在**家目录注册表**
`~/.config/obsidian-wiki/configs/<名>.json`（按 `--vault` 路径解析；未注册则回退库内 `<vault>/.wiki/config.json`）。数据留在 vault，代码随插件安装，配置在家目录。

> **给 Claude Code / Copilot CLI / CodeBuddy 及其它兼容 Agent-Skills 的 CLI**：三个 skill 在 `skills/` 下，宿主会自动发现，
> 直接用触发语（`/wiki-struct`、`/wiki-curate`、`/wiki-orchestrate` 或「整理笔记库」）即可。
> 各 skill 的完整流程、红线见对应 `skills/<name>/SKILL.md`。
>
> **给 Codex CLI（无 SKILL.md 斜杠系统）**：本文件即入口。按下文直接调脚本；需要 LLM 流程
> （`curate` 策展、`init` 插 marker、编排）时，**读对应 `skills/<name>/SKILL.md` 内联执行其步骤**。

## 三个 skill

| skill | 职责 | 确定性脚本（只读体检 / 重写受管块） |
|---|---|---|
| `wiki-struct` | 结构层：Home 总览树 / 各级 README / 分区页的受管块再生成 | `skills/wiki-struct/scripts/struct_gen.py check\|apply` |
| `wiki-curate` | 内容策展：ingest / curate / lint（写作规范与红线） | `skills/wiki-curate/scripts/lint.py lint` |
| `wiki-orchestrate` | 统一编排：只读体检 → 计划 → 按「结构→策展」调用上面两个 | 无脚本（playbook） |

`lib/wikicommon.py` 是各脚本共享库（脚本自带相对 import，无需配置）。

> spec-distill（SpecIn 需求 → vault 知识库沉淀）已于 v2.0.0 剥离，能力迁移到 specode 插件的 `/specode:distill <slug>`（写到各项目自己的 `knowledge-base/`）。

## 跑脚本

脚本是 Python 3 标准库、UTF-8、零外部依赖。**`--vault` 必填**，脚本经 `load_config` 按该路径在家目录注册表取配置（未注册则回退 `<vault>/.wiki/config.json`）。两者皆只读，仅向 `<vault>/<system_dir>/`（默认 `00-Index/_system/`）写体检报告。

脚本**通过对应 skill 触发执行**——`/wiki-struct` 进入 wiki-struct skill、`/wiki-curate` 进入 wiki-curate skill、`/wiki-orchestrate` 进入编排 skill。在 skill 上下文里用该 skill 的 **base directory 相对路径** `scripts/<脚本名>.py`（如 `scripts/struct_gen.py check --vault "$V"`、`scripts/lint.py lint --vault "$V"`）跑脚本，不解析环境变量、不 find 缓存。本文件是总纲，不是 skill、没有 base directory，因此**不在此给可直接运行的脚本命令**——运行入口在各 skill 的 SKILL.md。

## 首次配置（家目录多库注册表）

各库的结构配置存在家目录 `~/.config/obsidian-wiki/`（`vaults.json` 记各库 path+active，`configs/<名>.json` 存结构），**不写进 vault**。注册一个库是一次性设置——注册命令走 wiki-struct / wiki-orchestrate skill（它们在 skill 上下文里以 base directory 相对路径 `../../lib/registry.py` 调用 `registry.py`），或让用户在插件目录内手动跑：

```bash
python3 lib/registry.py register --name <短名> --path "/path/to/vault" --activate --config-from config.example.json
```

然后按你的目录名编辑 `~/.config/obsidian-wiki/configs/<短名>.json`（`index_dir` / `structure.dirs[]` / `lint` / `knowledge` 等）。
之后脚本传 `--vault <path>` 即按路径在注册表里取该库配置（未注册则回退库内 `<vault>/.wiki/config.json`）。
`registry.py list` 看全部、`resolve` 解析 active、`set-active --name <名>` 切库。

## 红线（所有 skill 共同遵守）

- 绝不修改 / 移动 / 重命名内容笔记原文；`wiki-struct` 只改 marker 包裹的受管块。
- SpecIn 只读；`10-Work/` 仅 `知识库/` 可写；敏感目录受管块只到文件名级。
- 破坏性 / 批量写前 tar 备份；写动作所在回合 append `<system_dir>/wiki-log.md`。
- 全程不外发 vault 内容。
