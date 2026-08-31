# UC-9 超时与守护（OrchestratorDaemon）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §3.3（超时非独立状态来源）、§6.1/§6.2（降级策略）、§18（OrchestratorDaemon）；`daemon.py`、`detect_timed_out_reviewers`（orchestrator.py:408）；GUIDELINES §6（超时/弃权场景库）；UC-5（弃权票计票）、UC-7 P4（人工裁定）。
- **边界声明**：守护进程**不读日志猜业务态、不解析语义**（FAQ Q10）；超时降级的结果（弃权票/人工裁定）最终仍通过 E3/E7/E9 生效；Layer 3 诊断报告**只给管理员**。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 活跃任务处于 `WAITING_REVIEW`（deadline 已在 UC-4 E2 记录） | 空转返回 `NONE` |
| P2 | `timeouts.per_reviewer` 已配置（如 `300s`） | E2 |
| P3 | daemon 拥有 State Store 独占写锁（或行级锁） | A3 |

## 2. 主成功场景

### a. 扫描循环

`macao daemon --once`（单次）或后台 `run_loop`（`poll_interval_sec` 轮询）；异常写 stderr、不裸 pass（Phase 3 已实现）。

### b. 识别超时席位

复用 `Orchestrator.detect_timed_out_reviewers`（单一事实源，禁止 daemon 自算第二套 deadline）：当前 ref/round 下未交合法票且过期的席位集合 T。

### c. 超时降级（PRD §6.2 顺序）

c1 对 T 逐席位 re-ping（一次，不轰炸）；c2 再等待宽限窗口（`grace_sec`，建议 60s）；c3 仍未交票 → 该席位记 **ABSTAIN 弃权票**（`confidence: 0.0`），审计 `REVIEWER_TIMEOUT_ABSTAIN`（detail：reviewer_id/review_round/checkpoint_ref）。

### d. 进入计票路径

T 作为 `timed_out_reviewers` 驱动共识评估（E3 → UC-5）：弃权票显式入票面（不进加权分母、计入法定人数判定）；结果三分支：
- 余票达双门槛 → 正常 APPROVED/REWORK_REQUIRED（弃权随终局 vote_result 落盘）
- 余票 DEADLOCK → UC-7 P4 人工接管（`HUMAN_OVERRIDE_REQUEST`，daemon 不自行裁定）
- 全体弃权 → 必然 DEADLOCK → UC-7

### e. 诊断报告（Layer 3，只给管理员）

超时席位附 `ui_hint` 级旁证（PTY 空闲/权限弹窗/进程崩溃重启），写入审计 detail 与管理员通知；**不据此推断任何业务结论**。

### f. 幂等与去重

同一席位同轮只记一次 ABSTAIN（重扫描不重复注入）；崩溃重启后已记弃权不重复、已收合法票优先于弃权标记（票到即覆盖 pending 弃权，先到先得按时间戳）。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 超时席位在宽限期内交票 | 撤销 pending ABSTAIN；正常收票；不产生弃权审计 |
| A2 | 宽限期内部分交票 | 交票者正常计票；未交者走 c3；互不影响 |
| A3 | 与 CLI/override 命令并发 | State Store 事务串行化；daemon 只做产物型触发（E3），命令型转移（E7 等）优先 |
| A4 | reviewer 席位被管理员临时标记弃权（Adapter 故障，PRD §14.4） | 等价于提前 c3；不走超时等待；审计区分 `manual_abstain` 与 `timeout_abstain` |
| A5 | 其他状态的超时（如 MERGING 停滞） | MVP 只定义 `WAITING_REVIEW` 席位级超时；全局停滞（60min 无进展 + 置信度<0.7 → E8 UNKNOWN）属运行期守护扩展，本用例仅登记 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 无活跃任务 / 非 `WAITING_REVIEW` | `action_taken: NONE`；不误伤 |
| E2 | 超时配置缺失/非法 | 启动失败并指出配置项；不默认无限等待 |
| E3 | daemon 自身崩溃重启 | 重启后按 DB 快照续扫：已记弃权不重复、已发 `HUMAN_OVERRIDE_REQUEST` 不重发（同轮 message_id 去重） |
| E4 | 弃权票注入后 Schema 落盘失败 | 事务回滚；席位保持超时未决；下轮扫描重试；不产生半张票 |

## 5. 后置条件

- **成功**：超时席位显式 ABSTAIN 入票面与审计；共识路径推进（E3/E7）；管理员收到诊断 ping（Layer 3 内容仅此通道）。
- **失败**：无部分弃权生效；任务态不变；daemon 存活。

## 6. 验收标准（可测）

1. 0s 超时 fixture（复用 `test_daemon_active_task_timeout_degradation`）：两位 reviewer 自动 ABSTAIN + 审计×2 + 进入计票
2. GUIDELINES §6 场景锁死：2-reviewer 1 超时+1 批准、2-reviewer 全弃权、超时后 E3 僵局 → UC-7——预期结果均可从本用例唯一推出
3. A1 宽限期内交票 → 无弃权记录；E3 重启重扫 → 审计不重复
4. daemon 代码审计：无日志语义解析、无业务态猜测、Layer 3 报告无执行者通道
5. 手工弃权（A4）与超时弃权审计可区分

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/daemon.py` | c1–c3 宽限与 re-ping、A1 撤销、E3 重启幂等 |
| `src/macao/workflow/orchestrator.py:detect_timed_out_reviewers` | 保持单一事实源；补 A4 手动弃权来源标记 |
| `src/macao/cli/main.py:daemon` | Layer 3 报告仅管理员通道 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 超时不是状态来源：一切降级最终经 E3/E7/E9 落地（PRD §3.3 原则在本用例重申）
- 弃权是**显式票**不是"缺席默认同意"——与 UC-4 fail-closed（缺票不编造）同一纪律
- 遗留决策点：①`grace_sec` 与 re-ping 策略可配置化；②E8 全局停滞检测的实现排期（建议 v1.1，先登记审计）
