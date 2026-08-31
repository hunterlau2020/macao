# UC-7 人工接管（`macao override resolve`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §3.3（E7/E9/E10）、§6.1（人工接管条件）、§6.2（降级策略）；GUIDELINES §8（真理不等于投票）；UC-5 b（DEADLOCK HOLD）；`resolve_override`（orchestrator.py:740）；FAQ Q16。
- **边界声明**：人工接管是**管理员的排他权力**。执行者不得自裁 `decision`（FAQ Q13）；评审者不得用投票打破互斥自报（GUIDELINES：真理不等于投票）；编排器只呈现证据、执行闭合选项、留痕。

---

## 1. 前置条件（接管触发条件，全部枚举闭合）

| # | 触发场景 | 进入态 |
|---|---|---|
| P1 | 计票 DEADLOCK（E3 HOLD，含 1:1、全弃权、占比均未达 2/3） | `CONSENSUS_CHECK` |
| P2 | `round ≥ max_rework_rounds` 仍返工 | `CONSENSUS_CHECK` |
| P3 | init 无法唯一识别 10 态（UC-1 h5；本用例复用同一选项集） | init 上下文 |
| P4 | 超时降级后人工裁定（UC-9 转入：ping 无应答 + 弃权 + 裁定请求） | `CONSENSUS_CHECK` |
| P5 | Git Conflict / MERGING 内不可自动恢复失败（UC-8 E4b 边界裁定） | `MERGING` |

## 2. 主成功场景

### a. 系统呈现证据（`macao override list`）

`HUMAN_OVERRIDE_REQUEST`（Type G，时限默认 10m）已发；`override list` 展示：任务态/ref/round、票面（含权重）、`issues_index`、诊断报告（Layer 2/3 预警、`ui_hint`）、冲突详情（P5 时 diff 摘要）。**只呈现，不推荐**——界面不得预选或排序暗示选项。

### b. 管理员裁定

`macao override resolve --choice APPROVED|REWORK|RETRY_REVIEW|CANCEL [--note <理由>]`（选项闭合，无其他值）。

### c. 编排器执行（确定性映射，PRD §3.3 E7）

| choice | 转移 | 语义 |
|---|---|---|
| `APPROVED` | → E4 → `MERGING` | 接受当前 checkpoint，进合并流水线 |
| `REWORK` | → E5 同规则 → `REWORK` | 返工（round+1）；裁定说明即返工依据 |
| `RETRY_REVIEW` | → E9 → `WAITING_REVIEW` | 本轮意见作废归档；round 不变；全新 `REVIEW_REQUEST`（新 message_id + 新 deadline） |
| `CANCEL` | → E10 → `CANCELLED`（终态） | 通知全员；现场归档 |

`--note` 建议必填但不强制（内容自由）；`choice` 非法值 → 拒绝（闭合枚举）。

### d. 终局落盘

裁定产生终局 `vote_result.json`（`resolution: human_override`，附 `signer`、note、票面快照）；P1/P4 场景下 UC-9 已注入的弃权票随终局一并写入（PRD §3.3：不提前写决策未定文件）。DEADLOCK HOLD 期间**不存在**中间版 vote_result。

### e. 留痕与回执

审计 `HUMAN_OVERRIDE_RESOLVED`（signer、choice、note、证据摘要哈希）；`docs/reviews/` 记录裁定件（GUIDELINES §1.3 命名：`<yyyy-MM-dd>-override-<task_id>-<signer>.md`）；agmsg 对请求方回执 ping（仅"已裁定 + 状态"，不含意见复述）。

### f. 超时未裁定

`HUMAN_OVERRIDE_REQUEST` 10m 时限到且无人裁定：**系统不得静默按高置信度继续**（GUIDELINES §6 场景）；保持 HOLD，升级提醒（re-ping 管理员 + Layer 3 报告只给管理员）；仍无响应则停留 HOLD 等待（MVP 不自动决策）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 裁定发生在 daemon 扫描间隙 | HOLD 态幂等：重复扫描不重复发 `HUMAN_OVERRIDE_REQUEST`（同轮去重，新 message_id 仅在重新触发时） |
| A2 | 多管理员并发裁定 | 先到者生效（State Store 事务串行化）；后到者收到"已裁定"回执；均入审计 |
| A3 | UC-1 h5 init 歧义 | 同一选项集（P3）；裁定写 `ADMIN_STATE_RESOLVED` 而非 vote_result；仅显式确认才写 `tasks.state` |
| A4 | 裁定 CANCEL 但 worktree 内有未回收会话 | E10 归档前强制 `adapter.stop` + worktree 清理；清理失败入审计 `CLEANUP_LEAKED`（不阻断终态） |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非接管态调用 `override resolve` | 拒绝（闭合触发条件 P1–P5）；提示当前态与 `next_action` |
| E2 | choice 非法 / note 超长 | 拒绝；note 截断上限（建议 4KB） |
| E3 | 执行者席位调用 | 拒绝（自裁禁令）；审计 `OVERRIDE_DENIED` |
| E4 | 裁定后落盘失败（Schema/磁盘） | 事务回滚：裁定不生效、保持 HOLD；审计 `OVERRIDE_PERSIST_FAILED`，可重试 |

## 5. 后置条件

- **成功**：终局 `vote_result.json`（`resolution: human_override`）或 init 裁定审计落盘；状态按 c 表转移；审计 + `docs/reviews/` 裁定件齐备。
- **失败**：保持 HOLD / 原状态；零部分生效。

## 6. 验收标准（可测）

1. P1–P5 各触发一次 → `override list` 证据字段齐备；四选项各自转移正确（E4/E5/E9/E10 映射）
2. DEADLOCK HOLD 期间 `vote_result.json` 不存在；裁定后存在且 `resolution=human_override`、弃权票并入
3. 10m 超时无裁定 → 仍 HOLD（不静默继续，GUIDELINES §6 反例场景锁死）
4. 执行者调用 → E3；非法 choice → E2；并发裁定 → A2 先到生效
5. 审计三件套（事件、裁定件、回执 ping）内容审计：ping 不含意见复述

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:override` | `list`/`resolve` 补证据视图、超时升级、A2 并发语义 |
| `src/macao/workflow/orchestrator.py:resolve_override` | P1–P5 触发闭合校验、终局 vote_result、审计 |
| `tests/` | 第 6 节（复用 `test_manual_override_resolution` 扩展） |

## 8. 设计自审

- 选项闭合 + 触发闭合：不给管理员开放枚举外的"自由发挥"，也不让系统在枚举外自创路径
- "静默继续"是本用例的头号反例（f 步锁死）；Layer 3 报告只给管理员（UC-9 同约定）
- 遗留决策点：①10m 时限与 re-ping 间隔可配置化；②多人管理员的法定裁定策略（v1.1，MVP 单管理员假设）
