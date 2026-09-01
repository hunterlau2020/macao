# UC-3 开发与检查点（`.dev.yml` 产物触发）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.5 §2.1（`.dev.yml` 规范）、§3.3（产物型转移 `CODING/REWORK → READY_FOR_REVIEW`、E6）、§3.4（产物生命周期）；FAQ Q13/Q14；UC-1 h0（三层载体）；`check_development_checkpoint`（orchestrator.py:202）。
- **边界声明**：执行者**独占**业务 commit、评审申请全文与 `.dev.yml` 内容；编排器只校验信封（Schema + 指针 + sha256 + `signal: EXPLICIT` + 新 commit 拓扑前进 + round 匹配），**不读、不写、不摘要**任何正文（FAQ Q10/Q13）。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务处于 `CODING` 或 `REWORK` | E1 |
| P2 | 本轮业务工作已产生**拓扑前进的新 commit**（严格为上轮 `checkpoint_ref` 之子孙且未被消费） | E2 |
| P3 | 申请全文已写入 `docs/reviews/<yyyy-MM-dd>-review-request-<mid>-*.md` | E3 |
| P4 | `.macao/.dev.yml` 按 §2.1 Schema 落盘，`signal: EXPLICIT` | E4 |
| P5 | `review_round` 与任务当前轮一致（返工轮 round+1） | E5 |

## 2. 主成功场景

### a. 执行者完成开发

在 `source_branch` 上提交新 commit（≥1）；测试、验收自检由执行者内容层负责，编排器不验证测试是否真的通过（仅登记 `quality_metrics` 自报字段）。

### b. 执行者写评审申请全文

`docs/reviews/<yyyy-MM-dd>-review-request-<mid>-<slug>.md`：变更说明、实现要点、验收对照、风险。**全文作者 = 执行者**；GUIDELINES §1.3 命名。编排器永不生成此文件。

### c. 执行者写 `.dev.yml`（摘要信封）

```yaml
version: "v2.5"
task_id: "task-1"
status: ready_for_review
signal: EXPLICIT
review_round: 1
executor: { id: "cc-ds4", cli: "claude-code" }
checkpoint_ref: "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
development:
  git: { latest_commit: "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678", source_branch: feature/x }
  quality_metrics: { tests_passed: true }   # 自报，编排器不复核
full_document:
  path: docs/reviews/2026-09-01-review-request-task-1-r1.md
  sha256: "<64位十六进制哈希>"
summary: "≤2KB 摘要（执行者写）"
```

### d. 编排器校验（Layer 1a，确定性）

d1 Schema（Draft-07）；d2 `signal == EXPLICIT`（隐式信号只预警不转移）；d3 **新 commit**：`checkpoint_ref != 上轮 ref` 且 `commit_exists`；d4 round 匹配；d5 `full_document.path` 存在且**字节级 sha256 对得上**——对不上即无效信封（fail-closed，UC-1 h0）；d6 归属：`executor.id` == 配置的 executor 席位。

### e. 产物型转移 → `READY_FOR_REVIEW`

锁定本轮 `checkpoint_ref`（评审对象硬绑定）；检查点窗口计时启动（1m，防旧信封滞留）；`agent_registry` 刷新：executor `role_view=CHECKPOINT_SUBMITTED`；审计 `CHECKPOINT_ACCEPTED`（ref、round、sha256）。

### f. 完成提示

`next_action=ROUTE_REVIEW`（→ UC-4）。编排器**不**在此步发 `REVIEW_REQUEST`（那是 E2 的事，见 UC-4）。

### g. 返工轮（`REWORK` 入口）

流程同 a–f，差异：申请全文须含**采纳清单**（按 UC-6，引用上轮 `issues_index` 的 `id`：采纳哪些、不采纳哪些及理由——内容由执行者写）；P5 校验 round+1；E6 转移触发（`REWORK → READY_FOR_REVIEW`），`checkpoint_ref` 更新。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | `signal: IMPLICIT`（未显式声明就绪） | 不转移；Layer 2 只产 `ui_hint` 预警（UC-1 h3a 同源），等显式信封 |
| A2 | 同轮提交第二份合法 `.dev.yml`（执行者修订） | 检查点窗口内以**最新合法信封**为准，旧信封标 `STALE` 不消费；窗口关闭后按首份消费（防抖动） |
| A3 | 手工补交（`macao checkpoint create --file`，PRD §14.2） | 允许；内容仍须过 d1–d6 全部校验，审计标注 `manual_supplement` 与提交者 |
| A4 | `quality_metrics.tests_passed: false` | 编排器不阻断（自报字段），但随 `REVIEW_REQUEST` 原样透传给评审者作为证据 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 任务态非 `CODING`/`REWORK` | 信封置 `STALE` 不消费；不转移；`next_action` 维持原值 |
| E2 | 无新 commit（ref 未变） | 拒绝：返工轮必须新 commit（PRD §15.2）；提示 UC-3 a |
| E3 | 全文路径不存在 | 信封无效（fail-closed）；审计 `CHECKPOINT_REJECTED`，原因 `full_document_missing` |
| E4 | Schema 不合法 | 同上，原因 `schema_invalid`；错误逐字段回报 |
| E5 | round 不匹配 | 置 `STALE`；返工轮未递增 → 提示按 round+1 重交 |
| E6 | sha256 对不上 | 信封无效（疑似正文被篡改/未同步）；**不猜测**，退回执行者重交 |

## 5. 后置条件

- **成功**：任务 `READY_FOR_REVIEW`；`checkpoint_ref` 锁定；信封 + 全文可被 UC-4 原样引用；审计含 sha256 链。
- **失败**：任务态不变；`.dev.yml` 标记无效/`STALE`；零 AEP 消息。

## 6. 验收标准（可测）

1. 正例：新 commit + 合法信封 + sha256 匹配 → `READY_FOR_REVIEW`；反例：E2/E3/E4/E5/E6 各自拒绝且任务态不变
2. `signal: IMPLICIT` 不转移（A1）；窗口内双信封取最新（A2）
3. sha256 篡改 fixture（改 1 字节全文）→ E6 拒绝
4. 返工轮：round 未 +1 → E5；采纳清单只出现在执行者产物，编排器产物中不得出现采纳语义字段（内容审计）
5. 编排器路径无 LLM 调用（单测断言）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/orchestrator.py:check_development_checkpoint` | 补 sha256/指针校验（h0(1) 回写）、STALE 语义、审计原因码 |
| `src/macao/core/schema.py` | `.dev.yml` Schema 增 `full_document{path,sha256}` 必填 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 三层载体严格执行（FAQ Q14）：agmsg 不传正文、yml 只当信封、全文在 `docs/reviews/`；sha256 把信封钉死在全文字节上
- "评审对象 = 合并对象"自本用例锁 ref 开始（UC-8 E4a 硬校验的起点）
- 遗留决策点：①检查点窗口时长（1m）与窗口后策略；②`quality_metrics` 自报字段是否演进为可选 CI 证据；③采纳清单是否独立 `adoption.yml`（UC-1 遗留⑤）
