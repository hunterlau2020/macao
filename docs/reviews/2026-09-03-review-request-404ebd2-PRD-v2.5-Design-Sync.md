# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单复审申请（Commit 404ebd2）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码与文档基线**：`commit 404ebd2`（`origin/main`）
- **前序受审基线与票型（`73576c5` 轮）**：
  - Claude (`NO_APPROVE`, P1×3), Codex (`REJECT`, P1×4), Grok (`NO_APPROVE`, P1×1), Muse (`YES_APPROVE`)
- **关联权威基准**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)（PRD v2.5 权威基准）
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与核心修复

针对专家委员会对前序基线 `73576c5` 指出的阻断项，团队在 `404ebd2` 落实了以下闭环：

1. **`review_disposition` Closed Schema 契约与示例规范化（Claude A-P1-1 / Grok P1-1）**：
   - 修正 [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) L159 示例中的字段：将 `generated_at:` 修正为契约规范定义的 `timestamp:`；
   - 在 `tests/test_prd_snippets_schema.py` 中新增自动化测试 `test_proposal_and_usecase_disposition_snippets`，断言提案与用例中的 disposition 示例 100% 通过 Draft-07 Schema 校验。
2. **编排器配置完整保留与早期纯加权门禁贯通（Claude A-P1-2 / Codex P1-1）**：
   - `Orchestrator.__init__`：全量保留 `self.raw_config`、`self.config["team"]`、`self.config["policy"]`，保证运行时策略与席位加权不被清洗丢失；
   - `collect_and_evaluate_consensus`：在组装选票前提取 `reviewer_weights` 与 `policy_cfg`，为选票打上准确加权与 `source: "manifest"`，早期仲裁调用 `ConsensusEngine.evaluate(votes=votes_list, configured_reviewers=num_configured, configured_weight=total_configured_weight, policy=policy_cfg)`；
   - DEADLOCK 分支与非 DEADLOCK 分支均全量传入 `task_id`、`reviewer_weights`、`policy` 与 `timeout_metadata`；
   - `VoteAggregator.generate_vote_result()` 中的 `policy_snapshot` 真实动态映射当前 `policy` 配置，彻底消除伪造缺省值。
3. **`submit_disposition()` 严密八重守卫实装（Claude A-P1-3 / Codex P1-2）**：
   - 实现并统一调用 `validate_disposition_fulfillment()`：
     1. 任务存在且严格处于 `CONSENSUS_CHECK`；
     2. 严格遵循 Draft-07 `review_disposition.schema.json`；
     3. 强制校验四元组绑定：`task_id`、`checkpoint_ref`、`review_round`、`executor.id`；
     4. 底层计票裁决必须为 `APPROVED`（或存在合法生效的管理员 `admin_override.json` 覆盖）；
     5. 物理存在 `.macao/vote_result.json`，且其实际字节哈希与 `vote_result_ref.sha256` 绝对一致；
     6. `issues_index_sha256` 与 `vote_result.json` 中的 `issues_index_sha256` 绝对一致；
     7. 缺陷穷尽覆盖性硬校验：`{d["issue_id"] for d in dispositions} == {i["issue_id"] for i in vote_result["issues_index"]}`（严禁漏报、伪造、多报）；
     8. 终态完整性硬校验：若 `disposition_status == "FINAL"`，严禁包含 `NEEDS_ADMIN` 处置项。
   - 新增 5 项负向与正向处置守卫回归测试。
4. **超时选票上下文元数据补齐（Codex P1-3）**：
   - `Orchestrator` 从 `REVIEW_REQUESTS_DISPATCHED` 审计记录中提取 `deadline` 与 `timestamp`，为超时合成选票注入 `source: "timeout"`、`weight`、`deadline` 与 `last_ping_at`，并在 `vote_result.json` 中完整落盘。
5. **D-1 计票不可变性守卫（Codex P1-4）**：
   - 在 `VoteAggregator.generate_vote_result(write_to_disk=True)` 中实装 D-1 不可变守卫：若 `.macao/vote_result.json` 已存在且针对相同 `(task_id, checkpoint_ref, review_round)`，则验证一致性并复用已有结论，严禁静默覆写；若检测到底层裁决冲突，则抛出 `ValueError` fail-closed 拦截。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：D-1～D-9 架构裁定、五重纯整数门禁、E7 两步 override、AEP/1.1 8 类消息、代码块示例 100% 过契约。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：8 份契约与 32 份 fixtures，强制反支配硬门禁、封闭 payload 与 `vote_result_ref` 必填约束。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：统一两步 override 规范与 E7 源态 `CONSENSUS_CHECK`，修正 disposition 示例为 `timestamp`。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐，E7 守卫与 PRD 权威表 100% 吻合。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 8 类 AEP 引用协议。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-1～F-22 全量作为设计约束。 |
| 8 | [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全量 142 份结论报告与 38 份申请。 |

---

## 3. 自动化验证结果

1. **PRD / 提案全量代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors, 0 Warnings）**。
2. **根配置语义与 Schema 校验**：`tests/test_config.py` **10/10 PASS**。
3. **加权计票五门禁、不可变性与反例推导**：`tests/test_consensus.py` **6/6 PASS**。
4. **全库文档控制字符扫描**：218 份 Markdown 文档 **0 控制字符（100% CLEAN）**。
5. **Schema 契约与 Fixtures 双向校验**：10 份正例 **10/10 PASS**，22 份反例 **22/22 准确拦截（FAIL-CLOSED）**；`docs/schemas/` 与 `src/macao/schemas/` **0 diff**。
6. **编排器端到端加权、处置防伪与回归套件**：`tests/test_p0_p1_rectification.py` **31/31 PASS**。
7. **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 101 tests — 100% OK（101/101 PASS）**。
8. **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

设计同步轨的前序全部阻断项均已完成代码、契约与文档级的物理闭环并接入测试门禁，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
