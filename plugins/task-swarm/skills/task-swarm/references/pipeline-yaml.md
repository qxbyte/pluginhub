---
description: Use when 编写或理解 task-swarm 的 pipeline.yml —— 任务编排的主格式(YAML 子集 + schema)。
---

# pipeline.yml — task-swarm 编排格式

pipeline.yml 是 task-swarm 的**主编排格式**(取代 legacy 的 markdown `tasks.md`)。用 `task_swarm.py init --pipeline <file>` 启动一次 run。

## 受限 YAML 子集

task-swarm 自带一个 stdlib parser，只支持 YAML 的一个子集：

- **支持**：block map(2 空格缩进)、block list(`- `)、flow list(`[a, b]`)、单行 scalar(str / int / `true` / `false` / null)、单/双引号字符串、`#` 注释。
- **不支持(会报错，带行号 + 构造名)**：block scalar(`|` / `>`)、flow map(`{k: v}`)、anchors / aliases(`&` / `*`)、多文档(`---`)、tags(`!!`)、嵌套 flow。
- bool 只认 `true` / `false`；`yes` / `no` / `on` / `off` 会被当作字符串。

## Schema

```yaml
version: 1
run:
  spec_id: user-login        # 可选
  max_parallel: 4            # 可选,默认 4
  max_rounds: 6              # 可选,默认 6
task_groups:                 # 必填,≥1(= 语义任务组)
  - id: g1                   # 必填,唯一
    name: "Q01 接口改造"      # 必填
    needs: []                # 可选;引用其它 task_group id(组间依赖)
    review:                  # 可选,默认 {reviewer: true, validator: true};M3 起 per-组生效
      reviewer: true
      validator: true
    tasks:                   # 必填,≥1(= 任务点)
      - id: g1.1             # 必填,唯一
        title: "改 controller"  # 必填
        writes: [src/a.py]   # 必填(coder),≥1;文件冲突 → 并发调度依据
        reads:  [src/base.py] # 可选
        requirements: ["1.1"] # 可选;需求回溯
```

## 用法

```sh
task_swarm.py init --pipeline pipeline.yml --workdir <项目根>
```

schema 校验失败或 YAML 越界 → 退出码 1 + 逐条错误，不建 run。

> 注：`review` 字段当前(M2)仅解析、暂用全局 `--skip-validator`；per-任务组生效见后续里程碑。markdown `tasks.md`(`--tasks`)为 legacy 路径，保留兼容，推荐用 pipeline.yml。
