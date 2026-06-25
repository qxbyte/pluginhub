# spec-distill v2 — 5 类 yml schema 模板

> `spec-distill sync` 写每篇知识 yml 时使用本模板。每个文件放到对应目录：
> `<project_root>/.ai-memory/knowledge/<category>/<knowledge_id>.yml`。
>
> 设计来自 `AI-Enterprise-Delivery-System/01-知识体系构建与优化方案.md`
> §4 L2 / L3 节，与 codemap-aimemory L0+L1 共存于同一 `.ai-memory/` 根。

---

## 公共字段（5 类共有）

```yaml
schema_version: "1.0"
knowledge_id: <prefix>-<kebab-slug>     # 文件名 stem（不带 .yml）
type: <见下表>                          # 类型一一对应 category
version: 1                              # 同 knowledge_id 升级时 +1
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
status: active                          # active / deprecated / draft
confidence: high                        # high / medium / low
source_spec: SpecIn/windows-Public/specs/<spec-dir>
source_files:
  - requirements.md
  - design.md
  - implementation-log.md
related_requirements:                   # spec_id / 需求号 列表
  - REQ-2024-0078
  - 121659
related_knowledge:                      # 同 .ai-memory/knowledge/ 内其它 .yml 的 knowledge_id
  - mod-order-pricing
  - rule-coupon-points-mutex
related_code:                           # 代码定位；codemap-aimemory entity 也可（fn-* / cls-* / tbl-*）
  - file: src/modules/order/pricing.js
    entity: calculateOrderPrice         # codemap entity_id 或函数名
    line_range: [120, 180]
  - file: src/modules/order/validators.js
    entity: validateCouponAndPoints
tags:
  - coupon
  - pricing
```

| category | type | ID 前缀 |
|---|---|---|
| `rules/` | `business_rule` | `rule-` |
| `business/` | `business_process` | `biz-` |
| `modules/` | `module_map` | `mod-` |
| `cases/` | `case` | `case-` |
| `pitfalls/` | `pitfall` | `pit-` |

---

## 1. `rules/<rule-*>.yml` — 业务规则 / 全局机制

公共字段之外，加：

```yaml
statement: "优惠券和积分抵扣不能同时使用"
why: "避免用户双重优惠导致亏损"
trigger_conditions:                     # 何时该规则生效
  - "下单时同时勾选优惠券和使用积分"
exceptions:                             # 反例 / 边界
  - "VIP 等级 ≥ 8 的用户例外，见 rule-vip-privilege"
enforcement:                            # 在代码哪一层强制
  - "service 层 validateCouponAndPoints() 抛异常"
  - "前端 OrderPricing.vue 互斥禁用"
```

---

## 2. `business/<biz-*>.yml` — 业务流程 / 功能页

```yaml
title: "Q01 承保送收付入库流程"
trigger: "承保系统下单完成"
end_state: "SfCreditMain + SfBusinessCredit 双表落库 + 推 ATP"
steps:
  - n: 1
    actor: "承保系统"
    action: "调用 Q01 接口"
    inputs: [policyNo, paymentComCode, codInd]
  - n: 2
    actor: "收付系统"
    action: "判断 paymentComCode 是否需要覆盖赋值"
    branches:
      - condition: "paymentComCode != centerCode"
        next: "覆盖为 centerCode"
      - condition: "paymentComCode == centerCode"
        next: "保留原值"
data_flow:                              # 表 / 接口 链路（可放 ascii 字符串）
  - "Q01 → SfCreditMain.PAYSTATUS = 0"
  - "Q17 / Q01 入库顺序约束：Q17 先于 Q01"
ui_constraints:                         # 功能页特有；非功能页留空
  - element: "保存按钮"
    rule: "未选优惠券时灰禁用"
```

---

## 3. `modules/<mod-*>.yml` — 表 / 字段 / 调用链 / 模块地图

```yaml
title: "SfCreditMain 字段说明"
scope: table                            # table / call_chain / module / api
entity_kind: table                      # codemap-aimemory 实体 kind 对齐
primary_entity: tbl-sf_credit_main
columns:                                # 仅 scope=table 时
  - name: PAYSTATUS
    type: TINYINT
    enum:
      - value: 0
        meaning: 未处理
      - value: 1
        meaning: 已确认
      - value: 3
        meaning: 部分确认（已作废，保留兼容）
  - name: CNY_PAY_AMOUNT
    type: DECIMAL(18,2)
    note: "实际归属 SfBusinessCredit，非 SfCreditMain 字段"
shard:                                  # 分库分表
  key: underwriteEndDate
  routing: SfRouter
  database: 主库
call_chain:                             # 仅 scope=call_chain 时
  - step: "前端 SfPlanAuthority.vue:142"
    next: "POST /api/payment/authorityQuery"
  - step: "Controller PaymentController.authorityQuery"
    next: "Service authorityQueryByPaymentNo"
```

---

## 4. `cases/<case-*>.yml` — 历史案例（每个 spec 必产 1 篇）

```yaml
case_id: case-REQ-2024-0078
spec_id: REQ-2024-0078                  # 与 spec 目录名 / specode spec_id 对齐
title: "订单列表增加按金额区间筛选"
implementation_summary: |
  在 OrderQueryService 增加 amountMin / amountMax 参数；
  前端 admin/order-list.vue 加范围输入框；使用 BigDecimal。
changed_files:
  - src/modules/order/query.js
  - src/modules/admin/order-list.vue
key_decisions:
  - decision: "使用 BigDecimal 避免浮点精度问题"
    reason: "金额查询历史踩过浮点 0.1+0.2=0.30000000000004 的坑"
  - decision: "复用已有的权限校验中间件"
    reason: "保持鉴权一致；不另起 middleware"
bugs_encountered:                       # 实施中遇到但已修；持久教训进 pitfalls/
  - "初始实现未处理金额为 null 的情况，validation 直接 NPE"
lessons:                                # 教训列出；可复用结论应另起 rule-/pit-
  - "涉及金额查询时，必须考虑 null 和 0 的边界"
review_findings:                        # 来自 review.md / validation.md
  - finding: "重复的金额校验逻辑"
    severity: minor
    action: "已抽到 amountValidator 工具方法"
acceptance_status: passed               # passed / failed / partial
```

---

## 5. `pitfalls/<pit-*>.yml` — 坑点（可复用的失败 / 修复经验）

```yaml
pit_id: pit-coupon-amount-null
title: "金额参数为 null 时未做兜底校验导致 NPE"
context: "电商订单计算价格、查询订单列表等所有涉及金额的接口"
symptom: |
  调用方未传 amount 字段时，BigDecimal.add 抛 NullPointerException；
  前端表现为接口 500，无明确错误码。
root_cause: |
  validator 假设 amount 必非 null，未走前置 Objects.requireNonNullElse；
  schema 未把 amount 标记为 required 也未给 default。
fix:
  - "validator 内 amountMin = Optional.ofNullable(amountMin).orElse(BigDecimal.ZERO)"
  - "OpenAPI schema 把 amountMin / amountMax 显式标 nullable=true + default=0"
prevention:                             # 怎么避免再犯
  - "新接口涉及金额查询时，必须 review null/0 兜底逻辑"
  - "PR 模板加一条 checklist: '金额参数是否处理 null'"
affects:                                # 这个坑可能影响哪里
  - "src/modules/order/query.js"
  - "src/modules/order/calculator.js"
first_seen_in: REQ-2024-0078            # 哪个 spec 第一次踩到
seen_again_in:                          # 后续重复踩到的 spec
  - REQ-2024-0092
```

---

## 各 yml 段内容来源对照

| 段 | 主要来自 spec 文档 | 备注 |
|---|---|---|
| 公共：`source_spec` / `source_files` / `related_requirements` | spec 目录 + frontmatter | 机器可写，无需 LLM 判断 |
| 公共：`related_code` | `design.md`、`implementation-log.md` | 抽 Java 类全名 / Vue 文件路径 / Mapper id |
| `rules.*` | `requirements.md` 业务约束部分、`design.md` 校验设计 | 抽"X 时不能 Y"型句子 |
| `business.*` | `design.md` 时序图 / 流程图、`requirements.md` 场景 | 步骤化为 `steps[]` |
| `modules.*` | `design.md` 数据模型 / 接口设计 | 字段枚举 / 调用链 / 分库分表键 |
| `cases.*` | `implementation-log.md`、`bugfix.md`、`tests`、`acceptance-checklist` | **每个 spec 必产 1 篇** — 记录本次实现 |
| `pitfalls.*` | `implementation-log.md`、`bugfix.md` | 仅"有复用价值的坑"独立成篇；临时调试不纳入 |

---

## 深度标准（参照现有 fin 语料的人脑可读版本）

- **modules 类**：字段枚举全列（含已作废值并标注）；分库分表键明确（`分表键 underwriteEndDate`）；调用链含完整 Java 类路径 + 方法名。
- **rules 类**：触发条件精确到字段比较；列出反例 / 边界条件。
- **business 类**：每步标注 actor + action + branches；功能页含 ui_constraints。
- **cases 类**：key_decisions 配 reason；bugs_encountered 含表面症状；lessons 是一句结论。
- **pitfalls 类**：symptom + root_cause + fix + prevention 四件套必填。

---

## 同名 ID 升级规则

如目标目录已有同 `knowledge_id`：

1. Read 原 yml 全文。
2. **不重写**：`title` / `statement` / `key_decisions` 等结构性字段保留。
3. **追加**：`related_requirements` 追加本次 spec；`source_files` 追加本次新读到的文件；`seen_again_in` / `bugs_encountered` 追加新条目。
4. **更新**：`updated_at` 改成今天；`version` +1。
5. **必要时分裂**：如本次新信息与原文相悖，AskUserQuestion 让用户选"覆盖 / 新建 -v2 后缀文件 / 跳过"。
