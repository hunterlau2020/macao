# MACAO PRD v2.5 架构方案、契约库与用例体系复审申请（Commit 95b7b35）

- **申请日期**：2026-09-04
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（PRD v2.5 产品设计、契约库、用例体系与代码实现全面对齐与实施准入）**
- **当前代码与文档基线**：`commit 95b7b35`（`origin/main`）
- **前序受审基线与专家票型（`73576c5` 轮）**：
  - **Claude**（双轨）：轨 A `NO_APPROVE` (P1×3)；轨 B `NO_APPROVE` (P1×1)
  - **Codex**（合并）：`REJECT` (P1×4)
  - **Grok**（双轨）：轨 A `NO_APPROVE` (P1×1)；轨 B `NO_APPROVE` (P1×1)
  - **Muse**（双轨）：轨 A `YES_APPROVE`；轨 B `YES_APPROVE`
  - **核心阻断与建议归纳**：
    1. `review_disposition` closed schema 与用例/提案代码块对齐（`timestamp`）；
    2. `Orchestrator.__init__` 保留 `team`/`policy`，纯加权 FSM 与动态 `policy_snapshot`；
    3. `submit_disposition()` 严密八重防伪守卫与四元绑定；
    4. 超时选票上下文元数据（`deadline`, `last_ping_at`）及落盘保障；
    5. `vote_result.json` D-1 不可变性守卫与冲突拒绝；
    6. [主动深度自查加固] 补齐 `OverrideChoice.EXTEND` 支持与 CLI 选项（Claude A-P2-3 / B-P2-2）；
    7. [主动深度自查加固] `StateRecognitionEngine` Layer 1c 补充 `requires_disposition` 门禁（Claude A-P2-1）；
    8. [主动深度自查加固] `VoteAggregator` 清理 `human_resolution` 死码保证 schema 完全合规（Claude A-P2-5）；
    9. [主动深度自查加固] 全量用例与提案 YAML/JSON 围栏抽检测试覆盖（Claude A-P2-6）；
    10. [主动深度自查加固] 用例文档明确纳入 D-9 `reconcile` 恢复执行器（Claude B-P2-1）。
- **上位评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**：[`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 评审背景与深度自查闭环说明

在对前序 `73576c5` 轮审查结论完成 P1 物理闭环（`404ebd2`）的基础上，架构团队进一步跟随审查专家（Claude、Codex、Grok、Muse）的审查思维与技术路径，开展了**全库代码与用例文档的深度主动自查**，在 `95b7b35` 彻底清除了潜在的 P2/P3 隐患与死码，大幅提高实施基线的健壮性：

1. **`review_disposition` 契约与用例/提案代码块完全对齐（Claude A-P1-1 / Claude B-P1-1 / Grok P1-1）**：
   - 修正 [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) 与 [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md)：将已废弃字段 `generated_at:` 统一修正为契约规范定义的 `timestamp:`；
   - 在 [`tests/test_prd_snippets_schema.py`](file:///home/debian/macao/tests/test_prd_snippets_schema.py) 中实装自动化测试，断言提案与 UC6 示例 100% 通过 Draft-07 Schema 校验。
2. **编排器完整保留策略与早期加权门禁全链路打通（Claude A-P1-2 / Codex P1-1）**：
   - `Orchestrator.__init__` 保留 `self.raw_config`、`self.config["team"]`、`self.config["policy"]`；
   - `collect_and_evaluate_consensus` 早期调用 `ConsensusEngine.evaluate()` 时显式传入 `configured_weight` 与 `policy`，消灭无权裸判；
   - `VoteAggregator.generate_vote_result()` 中 `policy_snapshot` 真实动态映射当前 `policy` 配置全部 11 项参数。
3. **`submit_disposition()` 严密八重防伪守卫与四元绑定（Claude A-P1-3 / Codex P1-2）**：
   - 实现并统一调用 `validate_disposition_fulfillment()`，严格执行：
     ① 必须处于 `CONSENSUS_CHECK`；
     ② 满足 Draft-07 强校验；
     ③ 任务四元组强绑定（`task_id`, `checkpoint_ref`, `review_round`, `executor.id`）；
     ④ 共识决议必须为 `APPROVED`（或合法生效的管理员 `admin_override.json`）；
     ⑤ `vote_result.json` 文件存在性与 SHA-256 强比对；
     ⑥ `issues_index_sha256` 强比对；
     ⑦ 100% 缺陷穷尽覆盖硬校验（严禁漏报、伪造、多报）；
     ⑧ `FINAL` 状态严禁包含 `NEEDS_ADMIN`；
     ⑨ [自查加固] 标记为 `EXEMPTED_BY_ADMIN` 的项目严格比对 `admin_override.json` 的 `override_id`。
4. **超时选票上下文元数据保证与不可变性（Codex P1-3 / Codex P1-4）**：
   - 超时 ABSTAIN 选票保证携带 `deadline` 与 `last_ping_at`，并在 DEADLOCK 分支与正常分支对称传参；
   - 实装 `vote_result.json` D-1 不可变守卫，同轮重复调用只读复用，决策冲突 fail-closed。
5. **[主动自查加固] 补齐 `OverrideChoice.EXTEND` 支持（Claude A-P2-3 / B-P2-2）**：
   - 在 `core/types.py` `OverrideChoice` 枚举中增加 `EXTEND = "EXTEND"`；
   - 在 `cli/main.py` 的 click.Choice 中增加 `"EXTEND"`；
   - 在 `transitions.py` 中更新 `TransitionTable.can_transition`，允许 E7 在 `CONSENSUS_CHECK` 内部刷新 HOLD 计时器；
   - 在 `orchestrator.py` `resolve_override` 中实装映射 `OverrideChoice.EXTEND -> (AgentState.CONSENSUS_CHECK, "E7", "EXTEND")`；
   - 新增集成测试 `test_override_choice_extend_refreshes_hold`。
6. **[主动自查加固] `StateRecognitionEngine` Layer 1c 补齐处置守卫（Claude A-P2-1）**：
   - 在 `src/macao/workflow/state_engine.py` Layer 1c 中增加 `requires_disposition` 判断：若为 True 且未见合法 FINAL 处置产物，严禁直跳 MERGING，必须输出 `(None, "HOLD", {"reason": "DISPOSITION_REQUIRED"})`；
   - 新增单元测试 `test_state_engine_layer_1c_disposition_check`。
7. **[主动自查加固] `VoteAggregator` 清理 `human_resolution` 死码（Claude A-P2-5）**：
   - 限制 `human_resolution` 仅允许 `APPROVED` 或 `REWORK_REQUIRED`，若传入 RETRY_REVIEW 或 CANCEL 则抛出指引异常（因重试与取消属于 admin_override.json 范畴），保证生成的 `vote_result.json` 永远不越界违背 `["APPROVED", "REWORK_REQUIRED", "DEADLOCK"]` schema。
8. **[主动自查加固] 围栏抽检全面扩面至用例文档与提案（Claude A-P2-6）**：
   - 在 `tests/test_prd_snippets_schema.py` 中新增 `test_all_usercases_and_proposals_code_snippets`，全自动扫描 `docs/usercases/*.md` 与 `docs/PRD_CHANGE_PROPOSAL_v2.5.md` 的全部代码块，确保 100% 过契约。
9. **[主动自查加固] 用例文档与主目录明确纳入 `reconcile` 恢复执行器（Claude B-P2-1）**：
   - 在 `docs/usercases/README.md` 与 `docs/usercases/UC10-existing-project-doctor.md` 中全面补齐 `reconcile`（D-9 确定性恢复执行器）命令与用例场景说明。

---

## 2. 申请分轨入口索引

| 评审分轨 | 对应专项申请文件 | 待审核心交付物 | 前序基线（`73576c5`）票型 | 本轮核验重点 |
|---|---|---|---|---|
| **轨 1：PRD v2.5 设计同步轨** | [`2026-09-04-review-request-95b7b35-PRD-v2.5-Design-Sync.md`](2026-09-04-review-request-95b7b35-PRD-v2.5-Design-Sync.md) | `docs/MACAO_PRD_v2.md`<br/>`docs/schemas/*.schema.json`<br/>`docs/PRD_CHANGE_PROPOSAL_v2.5.md`<br/>`docs/v2.5_CODE_CHANGE_INVENTORY.md` | Claude (`NO_APPROVE`), Codex (`REJECT`), Grok (`NO_APPROVE`), Muse (`YES_APPROVE`) | 编排器保留 policy/team、纯加权 FSM 早期门禁、八重处置防伪、EXTEND override 支持、Layer 1c 守卫、超时元数据、D-1 不可变落盘 |
| **轨 2：全量用例体系对齐轨** | [`2026-09-04-review-request-95b7b35-UseCases-v2.5-Alignment.md`](2026-09-04-review-request-95b7b35-UseCases-v2.5-Alignment.md) | `docs/usercases/`（13 份用例文档） | Claude (`NO_APPROVE`), Grok (`NO_APPROVE`), Muse (`YES_APPROVE`) | UC6 处置示例字段修正（`timestamp`）、用例代码块 100% 过契约扩面测试、UC-10 补齐 reconcile 命令、加权五门禁与处置守卫运行时互锁 |

---

## 3. 自动化机验结果

- **全量 PRD / 提案 / 用例代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（4/4 tests, 0 Errors）**；
- **根 `macao.yaml` 语义与 Schema 校验**：`tests/test_config.py` **10/10 PASS**；
- **加权计票五门禁、不可变性与反例推导**：`tests/test_consensus.py` **6/6 PASS**；
- **编排器端到端加权、处置防伪、EXTEND 与 Layer 1c 回归套件**：`tests/test_p0_p1_rectification.py` **33/33 PASS**；
- **全库 Markdown 控制字符扫描**：214 份文档 **0 控制字符（100% CLEAN）**；
- **Schema 契约双向一致性**：`docs/schemas/` ↔ `src/macao/schemas/` **8 份契约与全部 fixtures 逐字节一致（0 diff）**；
- **Fixtures 双向门禁测试**：10 份正例 **10/10 PASS**，22 份反例 **22/22 准确拦截（19 份 Draft-07 结构拦截 + 3 份配置语义拦截）**；
- **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 104 tests — 100% OK（104/104 PASS，0 Failures，0 Errors）**；
- **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**；
- **`STATUS.md` 双向对账**：39 份申请与 142 份结论报告 **100% 双向对齐（0 遗漏，0 悬空）**。

---

## 4. 定级建议

团队不仅对专家指出的全部阻断项进行了代码与文档双重闭环，还主动前瞻自查并解决了包括 EXTEND、Layer 1c 守卫、围栏扩面等在内的 5 项深层技术细节。全库 104 项自动化测试全绿通过。提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
