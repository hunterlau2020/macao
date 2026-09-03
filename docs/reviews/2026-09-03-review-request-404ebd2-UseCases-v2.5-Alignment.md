# MACAO 全量用例体系（UseCases）PRD v2.5 规格与 D-1～D-9 架构裁定对齐复审申请（Commit 404ebd2）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（用例文档体系与 PRD v2.5 实施基线全面对齐与准入）**
- **当前代码与文档基线**：`commit 404ebd2`（`origin/main`）
- **前序受审基线与票型（`73576c5` 轮）**：
  - Claude (`NO_APPROVE`, P1×1), Grok (`NO_APPROVE`, P1×1), Muse (`YES_APPROVE`)
- **关联权威基准**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)（PRD v2.5 权威基准）
- **关联变更提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 闭环稿，D-1～D-9 权威定义源）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）
- **关联评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)

---

## 1. 评审背景与核心说明

在 `73576c5` 评审轮中，Claude 与 Grok 审查专家均指出：`review_disposition` schema 封闭化后，[`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) L36 的代码块示例中残留了未定义的字段 `generated_at:`，导致机器校验被契约直接拦截。

本轮（`404ebd2`）对用例体系完成了彻底的规范化与契约互锁：
1. **UC6 处置示例字段修正**：将 `UC6-issue-triage-rework.md` L36 中的 `generated_at:` 修正为符合契约要求的 `timestamp:`，并通过了全量 Schema 校验器自动化拦截与通过测试（`test_proposal_and_usecase_disposition_snippets`）；
2. **处置防伪守卫运行时闭环（UC-6 / D-2 / D-5）**：编排器实装 UC-6 所定义的处置校验门禁，包括 100% 缺陷穷尽覆盖、任务四元组强绑定、vote_result 哈希比对以及 FINAL 状态下对 NEEDS_ADMIN 项的硬拦截；
3. **加权五门禁与不可变性运行时互锁（UC-5 / D-1 / D-6）**：完全打通加权计票、超时 ABSTAIN 上下文溯源（`deadline`, `last_ping_at`）与 D-1 不可变计票落盘。

---

## 2. 待审用例交付物全量清单

| # | 交付物文件 | 对应阶段 / 命令 | PRD v2.5 核心规格与单写者产物落地说明 | 契约与机验状态 |
|---|---|---|---|---|
| 1 | [`docs/usercases/README.md`](../usercases/README.md) | 用例目录与主旅程总览 | 确立主旅程流向（UC-5 $\rightarrow$ UC-6 $\rightarrow$ UC-8）与 5 大核心产物单一垄断写者规范表。 | 结构清晰，与架构一致 |
| 2 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | 产品事实源（F-1～F-22） | 落实 F-20：`vote_result.json` 为编排器单写不可变机器计票（D-1），`executor.disposition.yml` 为执行者单写独立处置产物（D-2）。 | 全量事实闭环 |
| 3 | [`docs/usercases/UC1-init-glm.md`](../usercases/UC1-init-glm.md)<br/>[`UC1-init-gemini.md`](../usercases/UC1-init-gemini.md) | `macao init` / `adopt` | 静态 `macao.yaml` 与动态 `agent_registry` 分离；统一 gitignore 9 规则与五重门禁纯整数公式。 | 契约校验 100% PASS |
| 4 | [`docs/usercases/UC2-task-create.md`](../usercases/UC2-task-create.md) | `IDLE` $\rightarrow$ `CODING` (E1) | 任务规划由人/执行者完成，编排器仅受理表单与 Schema 校验；下发 AEP/1.1 Type A `DEVELOPMENT_STARTED` 信封。 | 状态机严密 |
| 5 | [`docs/usercases/UC3-dev-checkpoint.md`](../usercases/UC3-dev-checkpoint.md) | `CODING`/`REWORK` $\rightarrow$ `READY_FOR_REVIEW` (E1/E6) | 执行者独占业务 commit 与申请全文；`.macao/.dev.yml`（`v2.5`）完整提供 `full_document` 与 `signal: EXPLICIT`；**返工轮严格要求拓扑单调前进的新 commit**。 | 拓扑子孙守卫严密 |
| 6 | [`docs/usercases/UC4-review-dispatch.md`](../usercases/UC4-review-dispatch.md) | `READY_FOR_REVIEW` $\rightarrow$ `WAITING_REVIEW` (E2) | 编排器原样派发 AEP/1.1 Type B `REVIEW_REQUEST`（10 个必需与语义 Context 块）；专家生成 `.review.yml` 与独立 worktree 隔离；**收敛触发条件修正为全席位 accounted**。 | 契约与分发隔离合规 |
| 7 | [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md) | `WAITING_REVIEW` $\rightarrow$ `CONSENSUS_CHECK` (E3) | **纯整数加权五重门禁**（D-6）；**不可变 `vote_result.json`**（D-1）；DEADLOCK 时即时落盘并 HOLD 问管理员（UC-7）。 | 算术与不可变性合规 |
| 8 | [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) | `CONSENSUS_CHECK` / `REWORK` | 执行者编写独立 `.macao/.dispositions/r<round>/executor.disposition.yml`（D-2）；修正 `timestamp:` 字段；精确穷尽覆盖 100% issue；`requires_new_checkpoint: boolean`（D-5）守卫分流；示例包含 `vote_result_ref`。 | 代码块 100% 过 Draft-07 契约 |
| 9 | [`docs/usercases/UC7-human-override.md`](../usercases/UC7-human-override.md) | 管理员人工接管 (`override resolve`) | DEADLOCK 时 `vote_result.json` 不可变，管理员裁定写入独立 `admin_override.json`；闭合 5 大选项；`APPROVED` 落盘 override 解除 HOLD 并投影 `SHOULD_DISPOSE` $\rightarrow$ 经执行者提交 FINAL disposition 校验后触发 E4 $\rightarrow$ `MERGING`。 | 源态与出口边完全一致 |
| 10| [`docs/usercases/UC8-merge-signoff.md`](../usercases/UC8-merge-signoff.md) | `MERGING` $\rightarrow$ `DONE` (E4a) | 评审对象 = 合并对象（`checkpoint_ref` 硬校验）；**六道关卡顺序执行**：关卡 1 Pre-merge Evidence 校验（远端共享 `ls-remote` fail-closed / 纯本地模式本地校验） $\rightarrow$ 关卡 2～6。 | 双轨合并关卡合规 |
| 11| [`docs/usercases/UC9-timeout-daemon.md`](../usercases/UC9-timeout-daemon.md) | 超时与守护 (OrchestratorDaemon) | 超时席位注入显式 `ABSTAIN`（`source: "timeout"`，含 `deadline` 与 `last_ping_at`）计入 `accounted` 席位以触发 E3，但**严格排除在非弃权有效集合（$E_N, E_W$）之外**；迟到票严格审计隔离。 | 边界与隔离机制合规 |
| 12| [`docs/usercases/UC10-existing-project-doctor.md`](../usercases/UC10-existing-project-doctor.md) | 既有项目接入与诊断 (`macao doctor`) | 零侵入只读体检（纯整数加权独裁帽、环境、Git 拓扑、gitignore 9 规则隔离、席位与产物一致性），发现冲突提示 `daemon --once` 对账。 | 只读体检边界合规 |
| 13| [`docs/usecases`](../usecases) | 路径别名软链接 | 指向 `docs/usercases`，保障跨文档与 CLI 引用的绝对兼容性。 | 符号链接有效 |

---

## 3. 自动化可复现验证结果

1. **全用例文档控制字符字节扫描**：`docs/usercases/*.md` **全部 13 份文档 0 控制字符（100% CLEAN）**。
2. **用例内嵌 YAML/JSON 示例契约校验**：
   - `UC6-issue-triage-rework.md` 处置示例 $\rightarrow$ `review_disposition.schema.json`：**100% PASS**（经 `test_prd_snippets_schema.py` 自动化核验）；
   - `UC3-dev-checkpoint.md` `.dev.yml` 示例 $\rightarrow$ `dev_manifest.schema.json`：**PASS**；
   - `UC1-init-gemini.md` `macao.yaml` 规格示例 $\rightarrow$ `macao_config.schema.json`：**PASS**。
3. **Draft-07 Schema 与 Fixture 双向校验**：
   - `docs/schemas/fixtures/valid/` 10 份正例 fixture：**10/10 PASS**；
   - `docs/schemas/fixtures/invalid/` 22 份反例 fixture：**22/22 100% 准确拦截（FAIL-CLOSED）**；
   - `docs/schemas/` 与 `src/macao/schemas/` 8 份同名契约：**0 diff，逐字节完全一致**。
4. **编排器端到端加权、处置防伪与回归套件**：`tests/test_p0_p1_rectification.py` **31/31 PASS**。
5. **全流程与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 101 tests — 100% OK（101/101 PASS，0 Failures，0 Errors）**。
6. **Python 代码静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

用例体系中 UC6 示例的 Schema 阻断项已彻底修复，且用例全部规则与运行时编排器守卫达成 100% 机械互锁与自动化验证。提请专家委员会维持授予并正式签署 **L1 DOC-ALIGNED / PG-0** 准入认证。
