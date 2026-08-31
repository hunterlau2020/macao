# UC-4 评审派发与审查（E2 派发 + 专家评审）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.4 §2.2（`.review.yml`）、§3.3（E2/E3）、§5（Reviewer Context）、§12.5（输出自愈）、§17.1（Worktree 派发）；FAQ Q14/Q16；GUIDELINES 全文；`dispatch_review_requests`（orchestrator.py:294）、`LiveAgentDispatcher`。
- **边界声明**：编排器是**邮差 + 规则机**：E2 把执行者已有 manifest **原样**放入 `REVIEW_REQUEST` 并 ping；评审正文、票面、问题索引全部由各专家写。编排器不归纳意见、不合并同类项、不代写摘要（FAQ Q13/Q15）。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务 `READY_FOR_REVIEW`，存在合法 `.dev.yml`（UC-3 d1–d6 通过） | E1 |
| P2 | 派发目标席位 `dispatchable`（Adapter preflight + capabilities + 已入队，UC-1 h4） | 席位级阻塞 A3 |
| P3 | 评审者满足 §12.2（`can_review` ∧ sandboxed ∧ `supports_worktree`） | E2 |
| P4 | 无本轮该 `reviewer_id` 已消费票（去重前置） | A5 |

## 2. 主成功场景

### a. 编排器执行 E2（命令型）

`READY_FOR_REVIEW → WAITING_REVIEW`；`.dev.yml` 标记 `consumed` 并归档 `.macao/archive/<ref>/r<round>/`；记录各评审者 deadline（`timeouts.per_reviewer`）。

### b. 构造 `REVIEW_REQUEST` 信封（零改写）

信封内容 = UC-3 的 manifest **原样引用** + 标准 Context 包（PRD §5.2）：`task_id`、`checkpoint_ref`、`review_round`、diff 获取方式（worktree 内 `git diff <target>..<ref>`）、`.dev.yml` 摘要、全文路径 + sha256、验收标准、评审方法指针（`MACAO_REVIEW_GUIDELINES.md`）。**编排器不增删摘要内容。**

### c. 派发到隔离 Worktree（§17.1）

对每名评审者：`.macao/worktrees/<agent_id>/<task_id>/r<round>` 独立 worktree（基于 `checkpoint_ref`）；适配器注入含 `review_round` 与 `diff` 的评审指令（§12.5）；未知 CLI 严格 `ValueError`（fail-closed，不软回退）。

### d. agmsg ping（通知，非结论）

每席位 ping 只含：`next_action=SHOULD_REVIEW`、短 SHA、`.dev.yml` 路径、全文路径。**不含**任务正文、编排者评论。

### e. 专家评审（内容层，全部由专家负责）

e1 在 worktree 内取 diff、读全文与验收标准；e2 评审结论全文写入 `docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md`（GUIDELINES §1.3 命名、§10 模板：L1–L4 结论、P0/P1 证据、行号）；e3 写 `.review.yml` 信封：`vote`（三值）、`opinion.status`、`issues[]`（id 带 `reviewer_id` 前缀、severity、one-line）、`full_document{path,sha256}`、`summary ≤2KB`；e4 方法遵循 GUIDELINES（四类证据、声明矩阵、反例库）。

### f. 编排器收票（Layer 1，确定性）

f1 Schema + sha256 对账（同 UC-3 d5，fail-closed）；f2 上下文强绑定：`checkpoint_ref`/`review_round`/`reviewer.id` 与派发目标一致（矛盾票拒绝，§17.2）；f3 输出自愈：多 YAML 块取**最后有效块**、矛盾 status/vote 拒绝（Phase 3 已实现）；f4 同 `reviewer_id` 重复票按 GUIDELINES 去重规则（保留有效票，审计 `REVIEW_DEDUP`）。

### g. 收敛

有效票 ≥ `minimum_quorum` → E3 进 UC-5；deadline 内未齐 → UC-9 超时守护接管。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 专家中途修正意见（重发 `.review.yml` + 新全文） | f4 去重取最新合法票；旧全文仍在 `docs/reviews/`（不删改历史） |
| A2 | 专家明确弃权（`vote: ABSTAIN`） | 合法票，计票路径（UC-5）；schema `ABSTAINED↔ABSTAIN` 互锁 |
| A3 | 个别席位 `dispatchable=false` | 调度结论不变（仍 `WAIT_OR_NOTIFY_REVIEWERS`）；该席位标阻塞，提示 `doctor`；法定人数按配置席位算，不静默缩分母 |
| A4 | CLI 输出杂乱（fenced 块缺失/ANSI 污染） | §12.5 两级自愈：strip_ansi → 块提取 → 整文兜底；自愈失败 = 无票（不编造，fail-closed） |
| A5 | 同 reviewer_id 两份同轮票 | f4 去重 + 审计；不双计 |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 无合法 `.dev.yml` 即请求派发 | 拒绝 E2；`next_action` 仍 `WAIT_OR_NOTIFY_EXECUTOR`（不倒逼执行者） |
| E2 | 评审者不满足 §12.2 能力矩阵 | 该席位不派发（E2 席位级）；管理员可临时标记弃权走 UC-9（PRD §14.4） |
| E3 | worktree 创建失败（Git 冲突/磁盘） | 该席位 `FAIL`，不阻断其余席位；审计 `DISPATCH_FAILED`；提示 `doctor` |
| E4 | sha256/上下文校验失败 | 该票无效（f2/f3）；不进计票；审计原因码 |
| E5 | 评审者进程崩溃重启后重复提交 | f4 去重幂等；崩溃前已消费票不重复计数 |

## 5. 后置条件

- **成功**：任务 `WAITING_REVIEW`；各评审者产出全文 + 信封齐备或 deadline 到期；所有信封可经 sha256 追溯到 `docs/reviews/` 全文。
- **失败（席位级）**：其余席位不受影响；无票席位交 UC-9。

## 6. 验收标准（可测）

1. E2 信封与 UC-3 manifest 逐字段一致（编排器零改写断言）
2. GUIDELINES §6 反例库逐场景推演：无关 YAML、缺票、矛盾票、重复票、错轮/错 ref → 全部拒绝或去重，预期结果可从本文唯一推出
3. `docs/reviews/` 命名与 §1.3 一致；ping 正文不含评审结论/摘要（内容审计）
4. worktree 物理创建与原子清理（复用 `test_live_dispatcher_worktree_mock_execution`）
5. 编排器路径无 LLM 调用；`issues[]` 的 id 均带 reviewer 前缀且未被改写

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/orchestrator.py:dispatch_review_requests` | E2 伴随动作补齐（归档、deadline、REVIEW_REQUEST 原样引用） |
| `src/macao/workflow/live_dispatcher.py` | f4 去重审计；A4 自愈路径补单测 |
| `docs/MACAO_PRD_v2.md` §5.2 | Context 包与三层载体（UC-1 h0）对齐回写 |
| `tests/` | 第 6 节 |

## 8. 设计自审

- 邮差语义：信封原样、ping 极短、全文在 docs/reviews/（FAQ Q14/Q16）
- fail-closed 全链：无票不编造、矛盾不调和、sha256 不符不消费
- 遗留决策点：①重发票的截流时限（建议 deadline 前 5m 停止去重更新）；②diff 体积上限（超限改传 path 让专家自取）
