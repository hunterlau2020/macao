# 专项评审申请：PRD v2.5 设计同步轨（Commit 95b7b35）

- **评审对象**：PRD v2.5 方案设计、契约库及运行时核心引擎实现
- **申请日期**：2026-09-04
- **当前 Commit**：`95b7b35`
- **对应全案申请**：[`2026-09-04-review-request-95b7b35.md`](2026-09-04-review-request-95b7b35.md)
- **重点复核模块**：
  1. [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)：意见处置代码块字段与契约 `timestamp` 对齐；
  2. [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py)：编排器完整保留 `policy`/`team`，纯加权 FSM 门禁贯通，八重处置防伪守卫与四元绑定；
  3. [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py) & [`src/macao/core/types.py`](../../src/macao/core/types.py) & [`src/macao/cli/main.py`](../../src/macao/cli/main.py)：实装 `OverrideChoice.EXTEND` 支持并在 FSM 允许 E7 内部刷新计时器（Claude A-P2-3 / B-P2-2）；
  4. [`src/macao/workflow/state_engine.py`](../../src/macao/workflow/state_engine.py)：Layer 1c 产物识别增加 `requires_disposition` 守卫（Claude A-P2-1）；
  5. [`src/macao/consensus/vote.py`](../../src/macao/consensus/vote.py)：超时 ABSTAIN 元数据保证，清理 `human_resolution` 死码（Claude A-P2-5），D-1 不可变落盘只读复用与冲突拦截；
  6. [`tests/test_p0_p1_rectification.py`](../../tests/test_p0_p1_rectification.py) & [`tests/test_prd_snippets_schema.py`](../../tests/test_prd_snippets_schema.py)：37 项专项测试 100% PASS。

---

## 逐项对账与自查清单

| 审查项 | 对应专家与编号 | 实装位置 | 验证结果 |
|---|---|---|---|
| 提案代码块 `generated_at:` 修正为 `timestamp:` | Claude A-P1-1 / Grok P1-1 | `docs/PRD_CHANGE_PROPOSAL_v2.5.md:159` | Draft-07 Schema 校验 PASS |
| 编排器保留 `team`/`policy` 与早期加权门禁贯通 | Claude A-P1-2 / Codex P1-1 | `src/macao/workflow/orchestrator.py:100-112, 590-645` | `test_orchestrator_preserves_policy_and_applies_weighted_consensus` PASS |
| 八重处置防伪守卫与四元绑定 | Claude A-P1-3 / Codex P1-2 | `src/macao/workflow/orchestrator.py:827-920` | `test_validate_disposition_fulfillment_comprehensive_guards` PASS |
| 超时选票元数据（`deadline`, `last_ping_at`）及落盘对称 | Codex P1-3 / Codex P1-4 | `src/macao/consensus/vote.py:150-165`, `orchestrator.py:603-630` | `test_timeout_metadata_in_vote_result_and_fallback` PASS |
| D-1 不可变结果落盘只读复用与冲突 fail-closed | Claude A-P1-3 / Codex P1-4 | `src/macao/consensus/vote.py:270-320` | `test_vote_result_immutability_and_conflict_rejection` PASS |
| 补齐 `OverrideChoice.EXTEND` 支持与 CLI 选项 | Claude A-P2-3 / B-P2-2 | `src/macao/core/types.py:70`, `cli/main.py:280`, `transitions.py:46`, `orchestrator.py:1037-1050` | `test_override_choice_extend_refreshes_hold` PASS |
| Layer 1c 补齐处置守卫 | Claude A-P2-1 | `src/macao/workflow/state_engine.py:102-118` | `test_state_engine_layer_1c_disposition_check` PASS |
| `human_resolution` 死码清理 | Claude A-P2-5 | `src/macao/consensus/vote.py:183-197` | vote_result 决议严格限定在 `["APPROVED", "REWORK_REQUIRED", "DEADLOCK"]` |
| 全量代码围栏 Draft-07 自动化抽检 | Claude A-P2-6 | `tests/test_prd_snippets_schema.py` | 4/4 测试 100% PASS |
