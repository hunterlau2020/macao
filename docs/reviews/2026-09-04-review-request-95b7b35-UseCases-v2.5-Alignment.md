# 专项评审申请：全量用例体系对齐轨（Commit 95b7b35）

- **评审对象**：MACAO PRD v2.5 全量用例体系（`docs/usercases/` 13 份分册）
- **申请日期**：2026-09-04
- **当前 Commit**：`95b7b35`
- **对应全案申请**：[`2026-09-04-review-request-95b7b35.md`](2026-09-04-review-request-95b7b35.md)
- **重点对账与自查清单**：
  1. [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md)：处置清单示例字段修正（`timestamp:`），完全对齐 Draft-07 closed schema（Claude B-P1-1 / Grok B-P1-1）；
  2. [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md)：明确赞成加权占比计算仅为报告与展示量，不参与门禁判定（Claude B-P3-1）；
  3. [`docs/usercases/README.md`](../usercases/README.md) & [`docs/usercases/UC10-existing-project-doctor.md`](../usercases/UC10-existing-project-doctor.md)：明确纳入 D-9 `reconcile` 确定性恢复执行器命令与用例场景（Claude B-P2-1）；
  4. [`tests/test_prd_snippets_schema.py`](../../tests/test_prd_snippets_schema.py)：实装全量用例代码块 Draft-07 Schema 自动提取与校验回归，覆盖率 100%；
  5. 运行时闭环：所有用例（UC-1 至 UC-10）与当前编排器、FSM 及加权共识算法无缝互锁。

---

## 逐项对账成果

| 用例编号与名称 | 核心修订与自查项 | 对应代码与契约状态 |
|---|---|---|
| **UC-1 初始化项目配置** | 吸收 `init` 与 `setup`，`macao.yaml` 声明加权规则；席位零差集校验 | `src/macao/cli/main.py:init` 实装，100% 匹配 |
| **UC-2 任务受理** | 显式 E1 触发，编排器不拆任务，下发 Type A 信封 | `tests/test_p0_p1_rectification.py` 覆盖 |
| **UC-3 开发与检查点** | 产物型 E1_PRODUCED / 返工轮 E6 严格要求全新拓扑 commit，严禁复用被消费 commit | `test_rework_unchanged_commit_fails_closed` PASS |
| **UC-4 评审派发与审查** | Type B 信封下发，只读挂载与隔离评审，零 base64 | 契约与分发逻辑一致 |
| **UC-5 共识计票** | 加权五重门禁（纯整数运算），百分比澄清为报告展示量，不可变落盘 | `ConsensusEngine.evaluate()` 纯整数运算 PASS |
| **UC-6 意见处置与返工** | 示例 `generated_at:` 修正为 `timestamp:`；八重防伪守卫；Layer 1c 守卫 | 契约 Draft-07 100% PASS |
| **UC-7 人工接管** | 实装 `OverrideChoice.EXTEND` 选项与 CLI 参数；支持 CONSENSUS_CHECK 刷新 HOLD | `test_override_choice_extend_refreshes_hold` PASS |
| **UC-8 合并与签字** | E4a 六道合并关卡与预合并证据链校验 | FF 控制器与合并管线覆盖 |
| **UC-9 超时守护** | 守卫注入超时 ABSTAIN 选票，补充 deadline/last_ping_at 元数据 | `test_reviewer_timeout_degradation_scenario` PASS |
| **UC-10 既有项目接入与诊断** | 明确纳入 `reconcile` 确定性恢复执行器（D-9）与只读 doctor 报告 | 文档与命令行完全对齐 |
