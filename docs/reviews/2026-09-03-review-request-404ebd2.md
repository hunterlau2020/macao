# MACAO PRD v2.5 架构方案、契约库与用例体系复审申请（Commit 404ebd2）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（PRD v2.5 产品设计、契约库、用例体系与代码实现全面对齐与实施准入）**
- **当前代码与文档基线**：`commit 404ebd2`（`origin/main`）
- **前序受审基线与专家票型（`73576c5` 轮）**：
  - **Claude**（双轨）：轨 A `NO_APPROVE` (P1×3)；轨 B `NO_APPROVE` (P1×1)
  - **Codex**（合并）：`REJECT` (P1×4)
  - **Grok**（双轨）：轨 A `NO_APPROVE` (P1×1)；轨 B `NO_APPROVE` (P1×1)
  - **Muse**（双轨）：轨 A `YES_APPROVE`；轨 B `YES_APPROVE`
  - **核心阻断项归纳**：
    1. `review_disposition` closed schema 拒绝了提案与 UC6 示例中的 `generated_at`（应为 `timestamp`）；
    2. `Orchestrator.__init__` 配置归一化清洗丢失 `team` 与 `policy`，导致计票前早期门禁无权比对、`policy_snapshot` 伪造固定默认值；
    3. `submit_disposition()` E4 守卫缺失任务/检查点/轮次/执行者四元绑定、哈希绑定、共识 APPROVED 状态校验与 100% 缺陷穷尽覆盖校验；
    4. 超时弃权票缺失 `deadline` 与 `last_ping_at`，DEADLOCK 分支缺失 `task_id`、`reviewer_weights`、`policy`；
    5. `vote_result.json` 可被覆盖覆写，缺乏 D-1 不可变性守卫。
- **上位评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**：[`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 评审背景与本轮物理闭环说明

在 `73576c5` 评审轮中，专家委员会指出了 5 项深层阻断项。架构团队已在 `404ebd2` 完成逐项代码实装、文档同步与回归门禁建设：

1. **`review_disposition` closed 契约与示例规范化（Claude A-P1-1 / Claude B-P1-1 / Grok P1-1）**：
   - 修正 [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) L159 与 [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) L36：将已废弃的字段 `generated_at:` 修正为契约规范定义的 `timestamp:`；
   - 在 `tests/test_prd_snippets_schema.py` 中新增 `test_proposal_and_usecase_disposition_snippets`，断言提案与 UC6 中的 disposition 代码块 100% 通过 `review_disposition.schema.json` 强校验。
2. **编排器配置完整保留与纯加权状态机全链路打通（Claude A-P1-2 / Codex P1-1）**：
   - 修正 `Orchestrator.__init__`：全量保留 `self.raw_config`、`self.config["team"]`、`self.config["policy"]`，彻底杜绝清洗时丢失配置项；
   - 重构 `collect_and_evaluate_consensus`：在组装 `votes_list` 前优先提取席位加权映射 `reviewer_weights` 与策略 `policy_cfg`，给所有选票注入 `weight: max(1, w)` 与 `source: "manifest"`；
   - 早期仲裁调用 `ConsensusEngine.evaluate(votes=votes_list, configured_reviewers=num_configured, configured_weight=total_configured_weight, policy=policy_cfg)`，杜绝无权裸判；
   - 在 DEADLOCK 分支与非 DEADLOCK 分支均全量传入 `task_id`、`reviewer_weights`、`policy` 与 `timeout_metadata`；
   - 重构 `VoteAggregator.generate_vote_result()` 中的 `policy_snapshot`：直接从运行时 `policy` 配置动态提取全部 11 项参数，不再硬编码缺省值。
3. **`submit_disposition()` 严密八重守卫实装（Claude A-P1-3 / Codex P1-2）**：
   - 在 `Orchestrator` 中实现 `validate_disposition_fulfillment(task_id, disposition_data)`，在 `submit_disposition()` 与共识收集处统一调用；
   - 强制实行八重防伪门禁：
     1. 任务存在且必须严格处于 `CONSENSUS_CHECK`；
     2. 必须完全符合 Draft-07 `review_disposition.schema.json`；
     3. 强制校验四元组绑定：`task_id`、`checkpoint_ref`、`review_round`、`executor.id`；
     4. 底层计票裁决必须为 `APPROVED`（或存在合法生效的管理员 `admin_override.json` 覆盖）；
     5. 物理存在 `.macao/vote_result.json`，且其实际字节哈希与 `vote_result_ref.sha256` 绝对一致；
     6. `issues_index_sha256` 与 `vote_result.json` 中的 `issues_index_sha256` 绝对一致；
     7. 缺陷穷尽覆盖性硬校验：`{d["issue_id"] for d in dispositions} == {i["issue_id"] for i in vote_result["issues_index"]}`（严禁漏报、伪造、多报）；
     8. 终态完整性硬校验：若 `disposition_status == "FINAL"`，严禁包含 `NEEDS_ADMIN` 处置项。
4. **超时选票上下文元数据补齐（Codex P1-3）**：
   - `Orchestrator` 从 `REVIEW_REQUESTS_DISPATCHED` 审计记录中提取 `deadline` 与 `timestamp`；
   - 为超时合成的 ABSTAIN 选票注入 `source: "timeout"`、`weight`、`deadline` 与 `last_ping_at`；
   - `VoteAggregator.generate_vote_result()` 接收 `timeout_metadata`，并在合成选票中完整落盘超时溯源字段。
5. **D-1 计票不可变性守卫（Codex P1-4）**：
   - 在 `VoteAggregator.generate_vote_result(write_to_disk=True)` 中实装 D-1 不可变守卫：若 `.macao/vote_result.json` 已存在且针对相同 `(task_id, checkpoint_ref, review_round)`，则验证一致性并复用已有结论，严禁静默覆写；若检测到底层裁决冲突，则抛出 `ValueError` fail-closed 拦截；
   - 在 `tests/test_consensus.py` 中新增 `TestVoteAggregatorImmutability.test_vote_result_immutability_and_conflict_rejection` 单元测试。

---

## 2. 申请分轨入口索引

| 评审分轨 | 对应专项申请文件 | 待审核心交付物 | 前序基线（`73576c5`）票型 | 本轮核验重点 |
|---|---|---|---|---|
| **轨 1：PRD v2.5 设计同步轨** | [`2026-09-03-review-request-404ebd2-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-404ebd2-PRD-v2.5-Design-Sync.md) | `docs/MACAO_PRD_v2.md`<br/>`docs/schemas/*.schema.json`<br/>`docs/PRD_CHANGE_PROPOSAL_v2.5.md`<br/>`docs/v2.5_CODE_CHANGE_INVENTORY.md` | Claude (`NO_APPROVE`), Codex (`REJECT`), Grok (`NO_APPROVE`), Muse (`YES_APPROVE`) | 编排器保留 policy/team、纯加权 FSM 早期门禁、八重处置守卫、超时元数据、D-1 不可变落盘 |
| **轨 2：全量用例体系对齐轨** | [`2026-09-03-review-request-404ebd2-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-404ebd2-UseCases-v2.5-Alignment.md) | `docs/usercases/`（13 份用例文档） | Claude (`NO_APPROVE`), Grok (`NO_APPROVE`), Muse (`YES_APPROVE`) | UC6 处置示例字段修正（`timestamp`）、用例代码块 100% 过契约、加权五门禁与处置守卫运行时互锁 |

---

## 3. 自动化机验结果

- **全量 PRD / 提案 / 用例代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（3/3 tests, 0 Errors）**；
- **根 `macao.yaml` 语义与 Schema 校验**：`tests/test_config.py` **10/10 PASS**；
- **加权计票五门禁、不可变性与反例推导**：`tests/test_consensus.py` **6/6 PASS**；
- **编排器端到端加权、处置防伪与回归套件**：`tests/test_p0_p1_rectification.py` **31/31 PASS**；
- **全库 Markdown 控制字符扫描**：218 份文档 **0 控制字符（100% CLEAN）**；
- **Schema 契约双向一致性**：`docs/schemas/` ↔ `src/macao/schemas/` **8 份契约与全部 fixtures 逐字节一致（0 diff）**；
- **Fixtures 双向门禁测试**：10 份正例 **10/10 PASS**，22 份反例 **22/22 100% 准确拦截（FAIL-CLOSED）**；
- **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 101 tests — 100% OK（101/101 PASS，0 Failures，0 Errors）**；
- **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**；
- **`STATUS.md` 双向对账**：38 份申请与 142 份结论报告 **100% 双向对齐（0 遗漏）**。

---

## 4. 定级建议

`73576c5` 轮专家提出的全部 5 项深层阻断项已彻底完成代码实装、契约修正、文档同步与 101 项全量自动化测试闭环。提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
