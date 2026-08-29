# L3 全量阻断项闭环独立复审（Codex）

- **评审日期**：2026-08-29
- **评审对象**：`4df059e..ea536ab`
- **评审申请**：`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **证据类型**：CODE / TEST / SPEC
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

`PYTHONPATH=src python3 -m unittest discover tests -v` 在 `ea536ab` 上实测 **49/49 PASS**，最大返工轮次守卫、脏工作区拒绝、Worktree 异常清理和 vote 结果写盘前校验等整改均有实质进展。

但是新增 timeout 测试并未驱动生产超时路径，而是由测试直接向 Orchestrator 断言哪些 reviewer 已超时；系统仍没有持久化 deadline、扫描/判定超时、ping/重试和升级处理。即使调用者注入超时名单，合成的 `ABSTAIN` 也不会进入最终 `vote_result.json`。此外，push 后校验失败会造成远端、本地分支和工作流状态分叉，artifact 消费账本使用了错误 reviewer key，task ID 仍只有 24-bit 随机后缀。

上述问题中有 3 项 P1。根据评审指引，L3 必须有真实超时场景证据，PG-1/PG-2 的 P0/P1 必须为零，因此当前申请不能通过。

## 2. 已确认项

- **TEST / VERIFIED**：49 项单元与回归测试全部通过。
- **CODE / VERIFIED**：达到最大返工轮次时不再提前写出自动 `vote_result.json`，并保持在 `CONSENSUS_CHECK` 等待人工接管（`src/macao/workflow/orchestrator.py:419-441`）。
- **CODE / VERIFIED**：MergeController 在合并前检查 tracked/staged 修改并 fail-closed；上一轮已确认的用户工作区直接数据丢失路径得到保护。
- **CODE / VERIFIED**：Worktree 部分创建失败后的物理清理方法已补齐并有专项测试。
- **CODE / VERIFIED**：vote result 在写盘前执行 Schema 校验，非法 human resolution fail-fast。

这些局部整改不消除下述阻断项，也不能外推为 L3 全场景通过。

## 3. P0：必须先解决

本轮未新增 P0。

## 4. P1：进入 L3 / PG-2 前必须解决

### P1-1：超时 reviewer 由调用者断言，生产系统没有真实超时判定路径

**状态**：CONTRADICTED
**证据**：`src/macao/workflow/orchestrator.py:313-317,339-346,373-388`；`tests/test_p0_p1_rectification.py:65-100`；`docs/MACAO_REVIEW_GUIDELINES.md:57-62`；`docs/MACAO_PRD_v2.md:123-129,832-849,1372`

`collect_and_evaluate_consensus()` 新增的 `timed_out_reviewers` 是调用者传入的名单。Review request 没有由生产流程持久化和消费 deadline，也没有生产 caller/scanner 根据当前时间计算该名单。现有测试直接传入 `timed_out_reviewers=["opencode"]`，因此验证的是“已知答案注入后的分支”，不是 reviewer 不响应后系统自行完成 deadline → ping/retry → timeout/abstain → escalation 的真实路径。

实际影响：生产 reviewer 永不响应时，任务仍可无限停留在 `WAITING_REVIEW`；评审指引列明的 L3 timeout 场景仍为 **CLAIM_ONLY**。

**验收标准**：

1. E2 分发时持久化每位 reviewer/本轮的 deadline；
2. 由生产调度器或可恢复 scanner 按 Orchestrator 时钟识别到期项，执行 PRD 规定的 ping、退避重试、弃权与升级；
3. 重启后可从持久化状态继续，处理幂等且不会重复投票；
4. 测试只推进可控时钟，不得直接传入预期超时 reviewer 名单。

### P1-2：合成的 timeout ABSTAIN 未写入终局 vote_result.json

**状态**：CONTRADICTED
**证据**：`src/macao/workflow/orchestrator.py:364-393,443-452,577-587`；`src/macao/consensus/vote.py:81-115,141-153`；`docs/MACAO_PRD_v2.md:305-318,832-834`

Orchestrator 仅把 timeout `ABSTAIN` 追加到临时 `votes_list` 用于本次决策；自动终局与人工 override 随后调用 `generate_vote_result()` 时，传入的仍只有 `collected_reviews`。`VoteAggregator` 又完全从 review manifests 重建 votes，并以 `len(reviews)` 生成 `reviewers_responded`。

因此在“1 approve + 1 timeout”场景经人工裁定后，终局文件会报告 `reviewers_responded=1`、`abstain=0`，既没有超时 reviewer 的 `ABSTAIN` 票，也没有相应审计票面。这与 PRD “超时弃权随 E7 终局结果落盘并计入 reviewers_responded”的要求直接矛盾。

**验收标准**：把 timeout disposition 作为本轮持久化共识输入，生成自动或人工终局产物时原样携带；专项测试必须读取磁盘上的最终 JSON，并断言 reviewer、`ABSTAIN`、timeout 标记、`reviewers_responded` 与 `vote_breakdown` 一致。

### P1-3：push 成功后的远端校验不确定态被错误地当作可本地回滚

**状态**：CONTRADICTED
**证据**：`src/macao/merge/controller.py:115-132`；`src/macao/workflow/orchestrator.py:507-527`

若 `git push` 已成功，而紧随其后的 `git ls-remote` 因临时网络故障返回失败或空输出，远端可能已经包含 checkpoint。当前代码会仅把本地目标分支 `reset --hard` 到 `pre_merge_head` 并返回失败；`execute_merge()` 随即把任务转到 `REWORK`。远端分支、本地分支与工作流状态由此可能指向三个不同事实。

远端 SHA mismatch 分支同样不能仅靠本地 reset 宣称“回滚”，因为代码没有执行并验证远端补偿操作。

**验收标准**：将 post-push 无法确认建模为独立的 indeterminate/HOLD 状态，进行有界重试并升级人工处理；只有通过 compare-and-set/受保护的远端回退且重新验证成功后，才能声明 rollback。测试应模拟“push 实际成功但 ls-remote 失败/空响应”。

## 5. P2/P3：可延期但必须登记

### P2-1：review artifact 的消费更新使用错误 reviewer key

**状态**：CONTRADICTED
**证据**：`src/macao/workflow/orchestrator.py:353-362`；`src/macao/workflow/fsm.py:97-112`；`src/macao/storage/store.py:95-104`

注册 artifact 时 reviewer ID 为 manifest 内的 `codex` 等值；归档时对 `codex.review.yml` 使用 `rev_file.stem`，得到的是 `codex.review`。`mark_artifact_consumed()` 的 UPDATE 要求 reviewer_id 精确匹配，所以更新不到已注册行。E2E 即使在磁盘生成了归档文件，SQLite 中 review artifacts 仍会保持 `consumed=0` 且 `archived_path` 为空，磁盘与账本不一致。

**验收标准**：从已解析 manifest 或统一文件名解析函数取得 reviewer ID；更新后检查 affected-row count，并在 E2E 中断言每份 review artifact 均 `consumed=1`、`archived_path` 存在且指向实际文件。

### P2-2：task ID 仅保留 24-bit UUID 熵，碰撞仍未被处理

**状态**：PARTIALLY_VERIFIED
**证据**：`src/macao/workflow/orchestrator.py:101-123`；`tests/test_p0_p1_rectification.py:48-63`

task ID 从纯秒级时间戳改善为“秒级时间戳 + 6 个十六进制字符”，但同一秒内仅有 24-bit 随机空间，且数据库唯一键冲突没有有界重试。按生日碰撞近似，同秒创建 1,000 个任务的碰撞概率约 2.9%，5,000 个超过 50%。当前 100 次顺序生成测试只证明该次样本未碰撞，不能证明唯一性。

**验收标准**：使用完整 UUID、ULID 或等价高熵标识；若仍依赖随机主键，捕获唯一键冲突并执行有界重试。固定时钟测试应覆盖冲突注入，而不只是抽样未发生碰撞。

## 6. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| EA536AB-P1-1 | P1 | Workflow/Orchestrator 实现方 | 下次 L3 申请前 | 待补 | OPEN |
| EA536AB-P1-2 | P1 | Consensus/Artifact 实现方 | 下次 L3 申请前 | 待补 | OPEN |
| EA536AB-P1-3 | P1 | MergeController 实现方 | 下次 L3 申请前 | 待补 | OPEN |
| EA536AB-P2-1 | P2 | Artifact/FSM 实现方 | PG-2 前或显式风险接受 | 待补 | OPEN |
| EA536AB-P2-2 | P2 | Workflow/ID 实现方 | PG-2 前或显式风险接受 | 待补 | OPEN |

## 7. 门禁判定

| 门禁/级别 | 判定 | 原因 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留此前已验证范围，不扩大 | 49 项测试通过，但本轮仍存在代码与 PRD 的明确偏差 |
| L3 SCENARIO-VERIFIED | **不通过** | 真实 timeout path 未实现，终局 timeout 票面不完整 |
| PG-1 | **不通过** | P1 未清零 |
| PG-2 | **不通过** | 继承 PG-1 失败，且远端一致性与 artifact 消费方账本不稳定 |

## 8. 建议闭环顺序与验收标准

1. 先实现可持久化、可恢复的 timeout/deadline/ping/escalation 状态机，并让终局产物保存 timeout `ABSTAIN`。
2. 将 push 后校验失败转为可恢复的不确定态，禁止以 local-only reset 表示远端回滚成功。
3. 修正 review artifact reviewer key，并让 E2E 核验磁盘与 SQLite 生命周期完全一致。
4. 将 task ID 升级为完整高熵标识或加入唯一键冲突重试。
5. 完成后重放全同意、1:1、1 approve + 1 timeout、全 timeout、重启恢复、push-success/verify-failure 和 artifact 归档场景，再申请 L3 / PG-2。

## 9. 交叉文档需做的文字修订

- `docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md` 中“增加超时判定”“完整测试超时 Reviewer 标记弃权”和“全部阻断项已闭环”的表述目前证据不足，应在整改后按真实生产路径重述。
- task ID 的 6 位 UUID 后缀只能描述为降低碰撞概率，不应表述为“保证并发唯一性”。
- “数据库跟踪 5 份”只能证明注册数量；在 reviewer key 修正并断言 consumed/archive 双账一致前，不能表述为完整 artifact 生命周期验证。

## 10. Reviewer 自审记录

- 本轮逐项检查了 timeout 的**产生来源**与终局产物，而非仅检查测试名称或中间内存决策。
- 每个 P1/P2 均附当前提交的文件路径、行号、具体矛盾与可执行验收标准。
- 49/49 PASS 只作为现有测试结果，不用于替代未覆盖的生产超时、远端不确定态和数据库账本反例。
- 未以 reviewer 数量或作者申请声明代替 CODE/SPEC 证据。
