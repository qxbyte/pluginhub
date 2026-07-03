# <feature> 实现计划

> specode tasks = 可执行计划（writing-plans 格式）。模型 / superpowers subagent-driven / executing-plans / task-swarm 均消费本文件。
> 每个 Task 用 `验证: AC-x` 回指 requirements 的验收标准；`- [ ]` 步骤走 TDD。
> `**Interfaces:**` 写清跨 Task 的签名契约——subagent / coder 只看自己的 Task，靠这块了解相邻 Task 的名字与类型。

**Goal:** <一句话本计划交付什么>

**Architecture:** <2-3 句方法摘要（完整设计见 design.md）>

**Tech Stack:** <关键技术 / 库>

---

## Task 1: <component>

**Files:**
- Create / Modify: `exact/path`
- Test: `tests/exact/path`

**Interfaces:**
- Consumes: <用到前序 Task 的什么——精确签名；无则省略本行>
- Produces: <后续 Task 依赖的什么——精确函数名 / 参数 / 返回类型；无则省略本行>

**验证:** AC-1

- [ ] Step 1: 写失败测试
- [ ] Step 2: 跑看失败
- [ ] Step 3: 最小实现
- [ ] Step 4: 跑绿
- [ ] Step 5: commit

## Task 2: <component>  (needs: Task 1)

**Files:** ...
**Interfaces:** ...
**验证:** AC-2
- [ ] ...
