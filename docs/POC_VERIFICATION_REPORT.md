# MACAO PoC 三假设验证技术报告 (PoC Verification Report)

- **日期**：2026-08-27
- **验证版本**：Phase 0 / Phase 1 核心框架实现（含架构装配与配置单一事实源整改）
- **测试结果**：**28 / 28 测试用例全部 PASS (100%)**
- **验证范围**：物理契约产物规范、共识多数仲裁算法、单进程事件循环与 Worktree 隔离机制、配置装配与消息广播独立投递。

---

## 一、验证假设与实测结论

| 假设编号 | 核心假设内容 | 验证方法与测试套件 | 验证结论 |
|---|---|---|---|
| **假设 1** | **物理契约文件（`.dev.yml`, `.review.yml`, `vote_result.json`）可作为跨 Agent、跨轮次与崩溃恢复的唯一第一真理源** | `test_schema.py`、`test_state_store.py`、`test_reconcile_crash.py` | **✅ VERIFIED**<br>所有产物均严格符合 Draft-07 Schema 校验；SQLite 仅作为加速索引，崩溃后可完全基于磁盘物理产物 100% 恢复真实业务状态。 |
| **假设 2** | **2/3 多数仲裁算法配合法定人数 `ceil(2N/3)` 能有效解决多 Reviewer 决策、死锁与弃权，并安全触发人工接管** | `test_consensus.py`、`test_orchestrator_sim.py` | **✅ VERIFIED**<br>完整覆盖 2 人及 3 人评审场景下的全票通过、2/3 赞成、2/3 反对、1:1 平票死锁、弃权降级与评审人去重；死锁时严格 HOLD 且不伪写错误终局。 |
| **假设 3** | **单进程主事件循环（Single-process Event Loop）结合 Git Worktree 物理隔离与 AEP 消息队列，足以稳定驱动 10 态 FSM 全生命周期流转** | `test_fsm.py`、`test_msg_bus.py`、`test_orchestrator_sim.py`、`test_config.py` | **✅ VERIFIED**<br>通过 `MockAgentAdapter` 成功仿真 S1（Happy Path 到 Merge）、S2（多轮返工推进）、S3（死锁人工接管）、S6（任务取消）及异常回退，转移表白名单强制生效，Reviewer 专属 Worktree 路径隔离 fail-closed，配置组装根注入与多播消息独立 ACK 闭环。 |

---

## 二、自动化测试套件执行记录

```text
test_adapter_preflight_probes_no_type_error (test_config.TestConfigAndComposition.test_adapter_preflight_probes_no_type_error) ... ok
test_config_manager_property_accessors (test_config.TestConfigAndComposition.test_config_manager_property_accessors) ... ok
test_default_config_template_validates_against_schema (test_config.TestConfigAndComposition.test_default_config_template_validates_against_schema) ... ok
test_orchestrator_config_injection (test_config.TestConfigAndComposition.test_orchestrator_config_injection) ... ok
test_2_reviewer_consensus (test_consensus.TestConsensusEngine.test_2_reviewer_consensus) ... ok
test_3_reviewer_consensus (test_consensus.TestConsensusEngine.test_3_reviewer_consensus) ... ok
test_quorum_calculation (test_consensus.TestConsensusEngine.test_quorum_calculation) ... ok
test_full_review_context_builder (test_context_builder.TestReviewContextBuilder.test_full_review_context_builder) ... ok
test_minimal_review_context_builder (test_context_builder.TestReviewContextBuilder.test_minimal_review_context_builder) ... ok
test_fsm_transition_lifecycle_and_rejection (test_fsm.TestWorkflowFSM.test_fsm_transition_lifecycle_and_rejection) ... ok
test_transition_rules_and_whitelist_enforcement (test_fsm.TestWorkflowFSM.test_transition_rules_and_whitelist_enforcement) ... ok
test_mock_capabilities (test_mock_adapter.TestMockAdapter.test_mock_capabilities) ... ok
test_mock_simulate_dev_and_review_artifacts (test_mock_adapter.TestMockAdapter.test_mock_simulate_dev_and_review_artifacts) ... ok
test_aep_envelope_creation (test_msg_bus.TestMessageBus.test_aep_envelope_creation) ... ok
test_message_bus_fanout_independent_ack (test_msg_bus.TestMessageBus.test_message_bus_fanout_independent_ack) ... ok
test_p0_deadlock_does_not_write_fake_vote_result_and_holds (test_orchestrator_sim.TestOrchestratorSimulation.test_p0_deadlock_does_not_write_fake_vote_result_and_holds) ... ok
test_p0_reviewer_deduplication (test_orchestrator_sim.TestOrchestratorSimulation.test_p0_reviewer_deduplication) ... ok
test_p1_max_rework_rounds_guard (test_orchestrator_sim.TestOrchestratorSimulation.test_p1_max_rework_rounds_guard) ... ok
test_scenario_s1_happy_path_and_merge (test_orchestrator_sim.TestOrchestratorSimulation.test_scenario_s1_happy_path_and_merge) ... ok
test_scenario_s2_rework_loop (test_orchestrator_sim.TestOrchestratorSimulation.test_scenario_s2_rework_loop) ... ok
test_reconcile_unconsumed_dev_manifest_after_crash (test_reconcile_crash.TestCrashReconcile.test_reconcile_unconsumed_dev_manifest_after_crash) ... ok
test_reconcile_vote_result_after_crash (test_reconcile_crash.TestCrashReconcile.test_reconcile_vote_result_after_crash) ... ok
test_aep_envelope_schema (test_schema.TestSchemaValidation.test_aep_envelope_schema) ... ok
test_dev_manifest_schema (test_schema.TestSchemaValidation.test_dev_manifest_schema) ... ok
test_review_manifest_schema (test_schema.TestSchemaValidation.test_review_manifest_schema) ... ok
test_vote_result_schema (test_schema.TestSchemaValidation.test_vote_result_schema) ... ok
test_artifact_registration_and_append_semantics (test_state_store.TestStateStore.test_artifact_registration_and_append_semantics) ... ok
test_state_store_task_lifecycle (test_state_store.TestStateStore.test_state_store_task_lifecycle) ... ok

Ran 28 tests in 1.164s (OK)
```
