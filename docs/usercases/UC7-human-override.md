# UC-7 人工接管（`macao override resolve`）

- **设计日期**：2026-09-01
- **状态**：用例设计稿（v2.5 规范）
- **关联**：PRD v2.5 §3.3（E7/E9/E10）、§6.1（人工接管条件）、§6.2（降级策略）；GUIDELINES §8（真理不等于投票）；UC-5（DEADLOCK 即时落盘与不可变性）；D-1 / D-2 架构裁定；FAQ Q16。
- **边界声明**：人工接管是**管理员的排他权力**。执行者不得自裁 `decision`（FAQ Q13）；评审者不得用投票打破互斥自报；编排器只呈现证据、执行闭合选项、留痕。**DEADLOCK 时已即时落盘不可变 `vote_result.json`，人工裁定写入独立 `admin_override.json`，严禁二次回写 `vote_result.json`**。

---

## 1. 前置条件（运行时接管触发条件，全部枚举闭合）

| # | 触发场景 | 进入态 | 接管机制说明 |
|---|---|---|---|
| P1 | 计票 DEADLOCK（E3 即时落盘 `decision: DEADLOCK`，进入 `CONSENSUS_CHECK` HOLD） | `CONSENSUS_CHECK` | 机器计票无多数派，Orchestrator 保持不可变 `vote_result.json` 并发出 Type H 信封进入 HOLD |
| P2 | 返工轮次超限（`round ≥ max_rework_rounds` 仍需返工） | `CONSENSUS_CHECK` | 达到最大返工轮次阈值，自动进入 HOLD 申请管理员裁定 |
| P3 | Disposition 超时未交（`timeouts.review_disposition` 到期） | `CONSENSUS_CHECK` | 执行者未在规定窗口内提交处置产物，触发超时保护进入 HOLD |
| P4 | 执行者声明 `NEEDS_ADMIN` 处置 | `CONSENSUS_CHECK` | 执行者在处置草稿中对特定争议 issue 标记 `NEEDS_ADMIN` 并请求管理员裁决 |

> **边界说明**：
> - **初始化歧义（Init Ambiguity）**：属于 `macao init` 向导交互流程（UC-1 步骤 3），通过交互式终端选择 10 态之一并记录 `ADMIN_STATE_RESOLVED`，不属于运行期 E7 接管。
> - **合并冲突（Git Conflict）**：合并流水线关卡 3 失败直接触发 `E4b` $\rightarrow$ `REWORK`（round+1）由执行者在工作分支解决；仅当连续解决失败达到 `max_rework_rounds` 时转入 P2 触发接管。

## 2. 主成功场景

### a. 系统呈现证据（`macao override list`）

`HUMAN_OVERRIDE_REQUEST`（Type H，时限默认 10m）已发；`override list` 展示：任务态/ref/round、票面（含权重）、`issues_index`、诊断报告（Layer 2/3 预警、`ui_hint`）。**只呈现，不推荐**——界面不得预选或排序暗示选项。

### b. 管理员裁定

`macao override resolve --choice APPROVED|REWORK|RETRY_REVIEW|CANCEL|EXTEND [--note <理由>] [--exempt-issue-ids <id1,id2>]`（选项闭合，无其他值）。

### c. 编排器执行（确定性映射，PRD §3.3 E7）

| choice | 转移 | 语义 |
|---|---|---|
| `APPROVED` | 落盘 `admin_override.json`（解 DEADLOCK HOLD，投影 `SHOULD_DISPOSE`）→ 经执行者 FINAL disposition 校验通过后触发 E4 → `MERGING` | 接受当前 checkpoint；管理员生成独立 `admin_override.json`（含 `override_id`，可选列出 `exempt_issue_ids`）；解除 DEADLOCK HOLD 并通知执行者（`role_view=SHOULD_DISPOSE`）；执行者在 `.macao/.dispositions/r<round>/executor.disposition.yml` 中将对应 issue 处置标记为 `EXEMPTED_BY_ADMIN`+`override_id`，提交 FINAL disposition（`requires_new_checkpoint: false`）；编排器校验通过后触发 E4 进入 `MERGING` 流水线。**严禁无 FINAL 直跳 MERGING，严禁管理员代写 disposition** |
| `REWORK` | → E5 同规则 → `REWORK` | 返工（round+1）；裁定说明即返工依据 |
| `RETRY_REVIEW` | → E9 → `WAITING_REVIEW` | 本轮意见作废归档；round 不变；全新 `REVIEW_REQUEST`（新 message_id + 新 deadline） |
| `CANCEL` | → E10 → `CANCELLED`（终态） | 通知全员；现场归档 |
| `EXTEND` | 保持 HOLD | 重置当前超时计时器，等待后续处置 |

`--note` 建议必填但不强制；`choice` 非法值 $\implies$ 拒绝。

### d. 独立落盘与不可变审计

裁定生成独立 `admin_override.json`（包含 `override_id`、`timestamp`、`task_id`、`checkpoint_ref`、`review_round`、`trigger`、`choice`、`admin_identity`、`exempt_issue_ids`、`note`）。**原 `vote_result.json` 保持不可变，严禁任何覆盖回写**。

### e. 留痕与回执

审计 `HUMAN_OVERRIDE_RESOLVED`（signer、choice、note、override_id、证据摘要哈希）；`docs/reviews/` 记录裁定件（GUIDELINES §1.3 命名：`<yyyy-MM-dd>-override-<task_id>-<signer>.md`）；agmsg 对请求方回执 ping（仅"已裁定 + 状态"，不含意见复述）。

### f. 超时未裁定

`HUMAN_OVERRIDE_REQUEST` 10m 时限到且无人裁定：**系统不得静默按高置信度继续**；保持 HOLD，升级提醒（re-ping 管理员 + Layer 3 报告只给管理员）；仍无响应则停留 HOLD 等待。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 裁定发生在 daemon 扫描间隙 | HOLD 态幂等：重复扫描不重复发 `HUMAN_OVERRIDE_REQUEST` |
| A2 | 多管理员并发裁定 | 先到者生效（State Store 事务串行化）；后到者收到"已裁定"回执；均入审计 |
| A3 | 裁定 CANCEL 但 worktree 内有未回收会话 | E10 归档前强制 `adapter.stop` + worktree 清理；清理失败入审计 `CLEANUP_LEAKED`（不阻断终态） |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 非接管态调用 `override resolve` | 拒绝（闭合触发条件 P1–P4）；提示当前态与 `next_action` |
| E2 | choice 非法 / note 超长 | 拒绝；note 截断上限（4KB） |
| E3 | 执行者席位调用 | 拒绝（自裁禁令）；审计 `OVERRIDE_DENIED` |
| E4 | 裁定后落盘失败（Schema/磁盘） | 事务回滚：裁定不生效、保持 HOLD；审计 `OVERRIDE_PERSIST_FAILED`，可重试 |

## 5. 后置条件

- **成功**：独立 `admin_override.json` 落盘，原 `vote_result.json` 保持不可变；状态按 c 表转移；审计 + `docs/reviews/` 裁定件齐备。
- **失败**：保持 HOLD / 原状态；零部分生效。

## 6. 验收标准（可测）

1. P1–P4 各触发一次 $\implies$ `override list` 证据字段齐备；五选项各自转移正确（E4/E5/E9/E10/EXTEND 映射）；
2. DEADLOCK HOLD 期间 `vote_result.json` 已经存在且 `decision=DEADLOCK`；裁定后生成独立 `admin_override.json`，`vote_result.json` 内容与哈希无任何改写；
3. 10m 超时无裁定 $\implies$ 仍 HOLD（不静默继续，GUIDELINES §6 反例场景锁死）；
4. 执行者调用 $\implies$ E3 拒绝；非法 choice $\implies$ E2 拒绝；并发裁定 $\implies$ A2 先到生效；
5. 审计三件套（事件、裁定件、回执 ping）内容审计：ping 不含意见复述。

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/cli/main.py:override` | `list`/`resolve` 补证据视图、超时升级、A2 并发语义、`--exempt-issue-ids` |
| `src/macao/workflow/orchestrator.py` | P1–P4 触发闭合校验、生成独立 `admin_override.json`、不可变 `vote_result.json` 保持、审计 |
| `tests/` | 复用 `test_manual_override_resolution` 扩展 |

## 8. 设计自审（Design Self-Review）

- **单写者垄断**：管理员独占 `admin_override.json`，严禁代写 `executor.disposition.yml`；
- **两步转移边自洽**：`APPROVED` 裁定仅解除 HOLD 并置执行者视角为 `SHOULD_DISPOSE`，必须由执行者出具 FINAL disposition 并经校验通过后方由编排器推进 E4 $\rightarrow$ `MERGING`；
- **反例防御**：非法 `choice`、非管理员执行、执行中落盘失败均触发 fail-closed 拦截，保持 HOLD。
