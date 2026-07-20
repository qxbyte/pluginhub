# Changelog — ragkit

## Unreleased

## 0.2.2 (2026-07-21) — 修 Kimi 安装失败 + Kimi SessionStart 接线

同 specode 6.5.1 的 Kimi 修复：`.kimi-plugin/marketplace.json` 改 Kimi 官方 schema（`version:"2"`/`id`/`source`）；`.kimi-plugin/plugin.json` 加 `sessionStart: {skill: "using-ragkit"}` + 新增 `skills/using-ragkit/SKILL.md`（会话启动 advisory：ragkit 四技能 + 防脱轨硬约束）；加 `skillInstructions`（Kimi 工具映射）。Kimi 无 SessionStart hook，改由清单字段注入。README Kimi 安装说明改为本地 clone。仍未真机验证。

## 0.2.1 (2026-07-20) — 云端后端兼容与容错

### Fixed

- **DashScope 兼容模式批大小超限**（`backend.py`）：`_BATCH` 由 16 降为 **10**。通义 `text-embedding-v4` 兼容模式单请求硬上限为 10 条，原值 16 会导致 embed/query 报 `400 InvalidParameter`（`batch size ... should not be larger than 10`）。
- **云端向量调用失败导致 query 崩溃**（`pipeline.py` + `ragkit.py`）：密钥失效 / 网络抖动 / sidecar 异常时，`_vector_rank` 原会抛异常使整个 query 中断；现捕获为新状态 `vector_error`，**自动降级到词汇+元数据路**，stderr 打印固定提示 + 失败详情，退出码仍为 0，与文档承诺的「无后端时降级仍可用」一致。
- **Windows 下 CLI 测试编码崩溃**（`tests/conftest.py`）：`run_cli` 显式 `encoding="utf-8"` + 子进程 `PYTHONIOENCODING`，修复 GBK 默认解码对 UTF-8 中文/emoji 输出的 `UnicodeDecodeError`。

### Added

- **云端 `batch_size` 覆盖**（`backend.py`）：`cloud` 配置可加 `"batch_size": <n>` 覆盖默认 10，供 OpenAI 等高上限端点调大以减少请求次数。
- **文档：API key 全局设置 + 强制走云端**（`README.md`、`skills/query/SKILL.md`）：补充各平台临时/永久设密钥命令（含 Windows `setx`）、本地已缓存时用 `"backend": "cloud"` 强制云端、`vector_error` 降级信号说明。
- **测试**：`test_pipeline_degrades_on_vector_backend_error`（降级不崩）、`test_cloud_encode_respects_batch_size_override`（batch 覆盖切分），批大小边界测试同步改为 `_BATCH=10`。共 47 passed。

## 0.2.0 (2026-07-20) — 多宿主适配：bootstrap 去宿主绑定 + CodeBuddy/Codex/Kimi 独立 manifest

ragkit 现在同时面向 Claude Code / CodeBuddy / Codex / Kimi 四个宿主。

- **bootstrap / hook 文案去宿主绑定**：`ragkit_hooks.py` 的 SessionStart 注入文案「用 `Skill` 工具按名调用」保留 `Skill` 工具名、补「（或宿主等价的 skill 调用机制）」；docstring 里「Claude Code natively discovers…」泛化为「Some hosts (e.g. Claude Code) natively discover…」，语义不变。emit 的嵌套 `hookSpecificOutput.additionalContext` 被 Claude Code / CodeBuddy / Codex 共同接受，一份 handler 通吃。
- **新增三宿主独立 manifest + hooks 变体**：`.codebuddy-plugin/plugin.json`（指向 `hooks/hooks.codebuddy.json`，用 `${CODEBUDDY_PLUGIN_ROOT}`）、`.codex-plugin/plugin.json`（指向 `hooks/hooks.codex.json`，用 `${PLUGIN_ROOT}`）、`.kimi-plugin/plugin.json`（最简 `skills` 形态），及三份根 catalog。注意 hooks 变体沿用 ragkit 自己的 `hooks/run-hook.sh` wrapper + `scripts/ragkit_hooks.py` handler。Codex/Kimi 的 schema 待实测（见 README 标注）。

## 0.1.7 (2026-07-08) — skill/hook 定位脚本回归 superpowers 范式（删 resolver 特殊处理）

- **skill 定位脚本回归 superpowers 范式（删掉所有 resolver 特殊处理）**。实证 superpowers 如何在 skill 里定位并执行脚本：纯**相对路径**（`scripts/x.sh`，脚本放 skill 目录）+ 模型用 host 提供的 `Base directory for this skill: <abs>` 拼绝对路径 + 脚本内部 `dirname $0` / `__file__` 自定位——**全程零环境变量、零 find、零 `${CLAUDE_PLUGIN_ROOT}`**。ragkit 之前那行 `R="${CLAUDE_PLUGIN_ROOT:-$CODEBUDDY_PLUGIN_ROOT}"; find ... ` 正是 superpowers 明确不做的特殊处理，也是 Windows 全部故障的根：探针实测 `${VAR:-default}` 被 host 插值器整体吞成空（Claude Code combined_dash=[]）、CodeBuddy 连简单 `${CLAUDE_PLUGIN_ROOT}` 都不注入且把多行 bash 压成一行。修法：四个 skill 执行段删掉 resolver + find，改为裸相对路径 `sh ../../scripts/run.sh ../../scripts/ragkit.py ...`（脚本共用、在插件根 `scripts/`，故相对 skill 目录为 `../../`；除深度外与 superpowers 手法一致）。
- **hook 去掉 `${VAR:-default}`**。对齐 superpowers 的 hook（Claude Code 用简单 `${CLAUDE_PLUGIN_ROOT}`、Codex 用 `${PLUGIN_ROOT}`、Cursor 用纯相对路径，从不用 `:-`）。`hooks.json` 的 command 改为简单 `${CLAUDE_PLUGIN_ROOT}`，消除同一个 `:-` 吞空隐患。

## 0.1.6 (2026-07-08) — 修 CodeBuddy frontmatter 解析失败（四 skill 坍缩成 skill.md）

- **修 CodeBuddy 上四个 skill 坍缩成一条 `skill.md` 命令（根因：frontmatter 解析失败）**。差异化定位：与 superpowers（CodeBuddy 上正常）逐项对比，布局 / plugin.json / 无 commands 全同，唯一差异是 `description` 的写法——ragkit 用**双引号包裹且内部含 `Trigger: `（冒号+空格）**。0.1.3 加双引号只骗过了 Claude Code 的 YAML 解析器，**没骗过 CodeBuddy 的**：CodeBuddy 解析整块 frontmatter 失败 → 回退到文件名 `SKILL.md` → 四个 skill 同名坍缩成一条 `skill.md`。修法：四个 `description` 改成 superpowers 那种**已被 CodeBuddy 实证可用**的朴素形态——去双引号、去反引号、把 `Trigger: ` 改成 `Trigger `（彻底消灭冒号+空格）；`claude plugin validate` 通过、45 测试全绿。
- **删除 query skill 的 `__env_probe__` 临时探针**（0.1.3 spike 遗留）。harness 变量形态诊断已完成，探针段清理，query skill 回归纯检索职责。

## 0.1.5 (2026-07-08) — 加 session-start bootstrap hook（无 command 也能在 CodeBuddy 出命令）

- **新增 `hooks/`（session-start bootstrap）**——这是 superpowers 无 command 却能触发/显示 skill 的关键,ragkit 之前缺这块。0.1.4 去掉 commands 后:**Claude Code 原生发现插件 skill、仍出 `/ragkit:*`;但 CodeBuddy 上没有 bootstrap 的插件 skill 是"死的"**(不出命令、模型也不主动调)——对上 superpowers porting 指南那句"bootstrap 就是整个集成,没有它 skill 文件是死的"。
- 新增文件:`hooks/hooks.json`(SessionStart)+ `hooks/run-hook.sh`(复用 specode 的纯 Python 探测启动器,不走 uv,已在同环境验证)+ `scripts/ragkit_hooks.py`(注入 bootstrap,镜像 spec_hooks.py 的 emit 格式)。
- bootstrap 内容:声明四个 skill(query/embed/status/eval)+ **防脱轨硬护栏**——只按名调 skill、绝不在文件系统搜 skill/脚本文件(插件在缓存目录不在项目里)、检索只准调 ragkit 脚本、严禁自己读 `.ragkit` 向量/装 numpy/手搓相似度、脚本失败即停报错。直接堵死执行记录-2 那种"绕开插件手搓检索"。

## 0.1.4 (2026-07-08) — 去 commands，skill 直接出斜杠（修记录 2 脱轨元凶）

- **删掉 `commands/` 目录**（4 个薄壳命令），并从 4 个 skill 去掉 `user-invocable: false`。Claude Code 里 command 已并入 skill——默认(不写 `user-invocable`)的 skill 自动就有 `/ragkit:*` 斜杠入口 + 模型自动调,两样都占。`/ragkit:query` 等入口不变,只是现在**直接由 skill 提供**。
- **根治"模型绕开插件手搓检索"**:旧 command body 那句 `Follow the plugin skill at skills/query/SKILL.md`（相对文件路径）会**诱导弱模型去项目目录搜该文件**(执行记录-2 实证:`Search **/skills/query/SKILL.md` in project → 0 命中 → 放弃插件、装 numpy 自己算)。去掉这层 command 间接,模型只能按名 `Skill(ragkit:query)`,不再被指去搜文件。
- specode 按名调用 `ragkit:query` 不受影响(skill 名不变)。`__env_probe__` 探针仍在(待 CodeBuddy 实跑)。

## 0.1.3 (2026-07-08) — 修 skill YAML + 临时探针 spike

- **修 frontmatter YAML 解析失败(P0)**：0.1.2 的四个 skill `description` 含 `Trigger: `（冒号+空格），未加引号导致 YAML 解析失败——`claude plugin validate` 报错、且**运行时 frontmatter 被整体静默丢弃**（name/description 全丢，影响 skill 发现）。修法：四个 description 全部加双引号。（同款 bug 也在 specode / task-swarm 的 skill 里，单独处理。）
- **临时探针 spike**：`skills/query/SKILL.md` 加 `__env_probe__` 哨兵——检索词为 `__env_probe__` 时不查询、改跑自包含 bash,打印各 harness 在 **skill 上下文**里提供的 `CLAUDE_SKILL_DIR` / `CLAUDE_PLUGIN_ROOT` / `CODEBUDDY_*` 变量、路径形态、及候选 resolver 是否命中。用于定死"harness 无关的 skill 脚本定位"最终写法(去掉 `${VAR:-default}` + `find`，消除 Windows msys 路径 bug)。正常检索不受影响,**下一版删探针、落地正式 resolver**。

## 0.1.2 (2026-07-06) — skill description 统一模板

- 四个 skill（embed / query / status / eval）的 frontmatter `description`（渐进式加载唯一常驻的元数据）统一为「Use when 场景 → 做什么 → Trigger 触发词/命令 → 边界」轻量模板：补上 `/ragkit:*` 触发命令与彼此的交叉引用边界（query↔embed↔status）。零行为变化。

## 0.1.1 (2026-07-05) — Discover 分类标签

- marketplace.json 加 `"category": "database"`，Discover 面板显示 `[database]` 标签。零行为变化。

## 0.1.0 (2026-07-03) — 初版发布

### Added

- **插件骨架**：`.claude-plugin/plugin.json`（版本 0.1.0）、`scripts/run.sh`、测试脚手架、4 个命令入口（embed / query / status / eval）。
- **三路召回 + RRF 融合**（`scripts/rag/channels.py` + `fuse.py`）：向量通道（余弦相似度）、词汇通道（BM25 风格 TF-IDF）、元数据通道（标题/标签关键词匹配），RRF 融合后按知识点去重，返回带 `ranked_by` 来源标注的定位卡片。
- **增量 embed + 退出码 3 固定块**（`cmd_embed`）：默认仅重嵌变更 chunk（按 `text_hash` 比对）；无向量后端时返回退出码 3，stdout 输出 ╭─ RagKit ─╮ 固定提示块（含本地模型安装命令与第三方 API 配置步骤），词汇 + 元数据索引同步落盘可降级使用。
- **status 漂移检测**（`cmd_status`）：报告 `n_docs_on_disk` / `n_docs_indexed` / `n_chunks` / `backend_resolved` / `index_stale`，并列出 `drift.missing_from_index` 与 `drift.deleted_on_disk`，支持 `--json`。
- **eval harness + 16 条 golden 问题**（`cmd_eval` + `scripts/rag/evalset.json`）：12 条 case bucket（收付/加密/授权场景）+ 4 条 navigation bucket，输出整体 `recall@top` + `MRR` 及按 bucket 分项，MISS 列表辅助调试；`--channels` 支持词汇基线与全通道对比。
- **4 个 Claude Code 技能**（`skills/embed|query|status|eval/SKILL.md`）：斜杠命令 `/ragkit:embed` / `/ragkit:query` / `/ragkit:status` / `/ragkit:eval`，含退出码 3 固定块转述规则和降级指引。
- **specode Tier-0 RagKit gate**（见 specode 5.2.0 CHANGELOG）：specode `retrieval.md` 新增 Tier-0 gate，检测到 `ragkit:query` skill + 已建索引时，requirements / design 的经验检索自动走多路召回；未安装 / 未建索引零成本跳过。
- **后端解析优先级**（`scripts/rag/backend.py`）：`显式 cfg > 本地模型已缓存 > 云端 API 已配置 > none`；5 个内置 preset（openai / qwen / zhipu / voyage / azure）；`uv run` sidecar（`ragkit_local_embed.py`）隔离 torch / sentence-transformers 重型依赖。
- **chunker**（`scripts/rag/chunker.py`）：按 H2/H3 切片，保留 frontmatter 元数据（category / title / description / source / tags）。
- **hermetic 测试套件**：45 个 pytest cases，全用 dummy 后端，无网络、无模型依赖。

### 验收数字（真实语料）

语料：`/Users/xueqiang/Git/knowledge-base`（30 cases + 18 navigation = 48 文档，146 chunks）；
本地后端 `local::Qwen/Qwen3-Embedding-0.6B`；通道权重经优化轮 E2c 选定（lexical 1.2）。

标准 golden 集（16 条真实需求式 query）：

```
词汇+元数据基线:  n=16  recall@5=0.9375  mrr=0.8125
全通道(优化后):   n=16  recall@5=0.9375  mrr=0.8250   ← ≥ 基线
共同 MISS: 按收付登记号查询授权的后端三步链路（语料仅有 paymentNo 字样，词面/语义均难桥接）
```

语义压力集（6 条同义改写 query：脱敏→打码、见费出单→先收保费后出单等）：

```
词汇+元数据基线:  n=6  recall@5=0.8333  mrr=0.5889
全通道(优化后):   n=6  recall@5=0.8333  mrr=0.6111   ← 向量路对改写措辞的增益
共同 MISS: 水单号查授权信息走哪几步（行业黑话，向量亦无法桥接）
```

优化轮结论：TOP_CHUNK_HITS 与 RRF k 不敏感；通道权重是唯一有效杠杆，
lexical 1.2 是两个评测集上全通道均 ≥ 各自基线的唯一配置（详见 Obsidian ragkit-test-report）。
