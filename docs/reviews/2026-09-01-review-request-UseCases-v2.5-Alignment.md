# MACAO 全量用例体系（UseCases）PRD v2.5 规格与 D-1～D-9 架构裁定对齐评审申请

- **申请日期**：2026-09-01
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（用例文档体系与 PRD v2.5 实施基线全面对齐与准入）**
- **当前代码与文档基线**：`commit 5583bdd`（`origin/main`）
- **关联权威基准**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)（PRD v2.5 权威基准）
- **关联变更提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 闭环稿，D-1～D-9 权威定义源）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）
- **关联评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)

---

## 1. 评审背景与申请目标

在完成 PRD v2.5 核心正文、Draft-07 机器契约库以及编排引擎核心对 D-1～D-9 架构裁定的全面同步后，MACAO 全量用例文档体系（位于 [`docs/usercases/`](../usercases/) 及软链接 [`docs/usecases/`](../usecases/)）作为后续功能编码、测试套件编写与端到端系统演练的**场景化操作规范**，必须与最新产品规格达成 100% 机器语义级对齐。

针对专家委员会对前序提交提出的全部阻断项（包括处置路径分裂 B-1、AEP Type 字母错位 B-2、`items[]` 字段名 B-3、UC-8 Pre-merge Evidence 关卡 B-4、UC-3/UC-1 契约合规 B-5、D-1～D-9 权威编号对齐 B-6 等），本申请涵盖的全量 **13 份用例文档**已完成全面物理闭环，现提请专家委员会进行终局定级评审。

---

## 2. 待审用例交付物全量清单

| # | 交付物文件 | 对应阶段 / 命令 | PRD v2.5 核心规格与单写者产物落地说明 |
|---|---|---|---|
| 1 | [`docs/usercases/README.md`](../usercases/README.md) | 用例目录与主旅程总览 | 1. 确立主旅程流向：`UC-5 计票` $\rightarrow$ `UC-6 处置 (E5/E5a)` $\rightarrow$ `UC-8 合并 (E4/E4a)`；<br/>2. 建立 5 大核心产物单一垄断写者规范表（含统一路径 `.macao/.dispositions/r<round>/executor.disposition.yml` 与 `items[]` 契约字段）。 |
| 2 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | 产品事实源（F-1～F-22） | 落实 F-20：`vote_result.json` 为编排器单写不可变机器计票（D-1），`executor.disposition.yml` 为执行者单写独立处置产物（D-2）。 |
| 3 | [`docs/usercases/UC1-init-glm.md`](../usercases/UC1-init-glm.md)<br/>[`UC1-init-gemini.md`](../usercases/UC1-init-gemini.md) | `macao init` / `adopt` | 1. 静态 `macao.yaml`（v2.5 全量加权与预算配置）与动态 `agent_registry` 分离；<br/>2. 依据工作区特征识别 10 态，推不出唯一态则问管理员；<br/>3. agmsg 仅作通知 short ping，正文零模型语义依赖。 |
| 4 | [`docs/usercases/UC2-task-create.md`](../usercases/UC2-task-create.md) | `IDLE` $\rightarrow$ `CODING` (E1) | 1. 任务规划由人/执行者完成，编排器仅受理表单与 Schema 校验；<br/>2. 下发 AEP/1.1 Type A `DEVELOPMENT_STARTED` 信封，严禁自拟需求。 |
| 5 | [`docs/usercases/UC3-dev-checkpoint.md`](../usercases/UC3-dev-checkpoint.md) | `CODING`/`REWORK` $\rightarrow$ `READY_FOR_REVIEW` (E1/E6) | 1. 执行者独占业务 commit 与申请全文；<br/>2. `.macao/.dev.yml`（`v2.5`）完整提供 `full_document{path,evidence_commit,sha256}` 与 `signal: EXPLICIT`；<br/>3. **返工轮严格要求拓扑单调前进的新 commit**（必须为上轮 checkpoint 之子孙且未被消费），反向引用上轮 FINAL disposition。 |
| 6 | [`docs/usercases/UC4-review-dispatch.md`](../usercases/UC4-review-dispatch.md) | `READY_FOR_REVIEW` $\rightarrow$ `WAITING_REVIEW` (E2) | 1. 编排器原样派发 AEP/1.1 Type B `REVIEW_REQUEST`（零 base64，10 个必需与语义 Context 块）；<br/>2. 专家生成 `.review.yml`（契约属性 `items[]`）与独立 worktree 隔离；<br/>3. **收敛触发条件修正为全席位 accounted**（`accounted == configured`）。 |
| 7 | [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md) | `WAITING_REVIEW` $\rightarrow$ `CONSENSUS_CHECK` (E3) | 1. **纯整数加权五重门禁**（D-6：独裁帽 $3w_i < 2W$、席位法定人数 $E_N \ge \lceil 2N/3 \rceil$、权重法定人数 $E_W \ge \lceil 2W/3 \rceil$、胜方权重 $3W_{win} \ge 2E_W$、胜方席位 $\ge 2$）；<br/>2. **不可变 `vote_result.json`**（D-1）：三态决策（`APPROVED`, `REWORK_REQUIRED`, `DEADLOCK`），`issues_index` 原样拼接，声明 `requires_disposition: boolean`；<br/>3. DEADLOCK 时即时落盘并 HOLD 问管理员（UC-7）。 |
| 8 | [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) | `CONSENSUS_CHECK` / `REWORK` | 1. 执行者编写独立 `.macao/.dispositions/r<round>/executor.disposition.yml`（D-2，三态：`DRAFT` / `PENDING_ADMIN` / `FINAL`）；<br/>2. 精确穷尽覆盖 100% issue，`FINAL` 严禁遗留 `NEEDS_ADMIN`；<br/>3. `requires_new_checkpoint: boolean`（D-5）守卫分流：全 false 且 APPROVED $\rightarrow$ E4 进入 `MERGING`；任一 true $\rightarrow$ E5a 进入 `REWORK`；<br/>4. 管理员豁免流明确由执行者读取 `admin_override.json` 并提交带 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL disposition。 |
| 9 | [`docs/usercases/UC7-human-override.md`](../usercases/UC7-human-override.md) | 管理员人工接管 (`override resolve`) | 1. **严格落地 D-1**：DEADLOCK 时 `vote_result.json` 不可变，管理员裁定写入独立 `admin_override.json`；<br/>2. 闭合 5 大选项（`APPROVED`, `REWORK`, `RETRY_REVIEW`, `CANCEL`, `EXTEND`）并支持 `--exempt-issue-ids` 局部豁免。 |
| 10| [`docs/usercases/UC8-merge-signoff.md`](../usercases/UC8-merge-signoff.md) | `MERGING` $\rightarrow$ `DONE` (E4a) | 1. 评审对象 = 合并对象（`checkpoint_ref` 硬校验）；<br/>2. **六道关卡顺序执行**：关卡 1 Pre-merge Evidence Push 校验（`ls-remote` 校验 `refs/macao/evidence/<task_id>/r<round>` 已推送） $\rightarrow$ 关卡 2 检出 $\rightarrow$ 关卡 3 技术合并 $\rightarrow$ 关卡 4 CI gate $\rightarrow$ 关卡 5 人工签字 $\rightarrow$ 关卡 6 源码推送与 Post-merge 封存归档；<br/>3. 杜绝“源码已合并而证据未落地”的审计断裂。 |
| 11| [`docs/usercases/UC9-timeout-daemon.md`](../usercases/UC9-timeout-daemon.md) | 超时与守护 (OrchestratorDaemon) | 1. 超时席位注入显式 `ABSTAIN`（D-3：`source: "timeout"`）计入 `accounted` 席位以触发 E3，但**严格排除在非弃权有效集合（$E_N, E_W$）之外**；<br/>2. 迟到票边界：计票前可替换 pending 标记，`vote_result.json` 落盘后严格作为 `LATE_REVIEW_ISOLATED` 审计日志隔离，不修改投票结果。 |
| 12| [`docs/usercases/UC10-existing-project-doctor.md`](../usercases/UC10-existing-project-doctor.md) | 既有项目接入与诊断 (`macao doctor`) | 零侵入只读体检（D-9：纯整数加权独裁帽、环境、Git 拓扑、gitignore 9 规则隔离、席位与产物一致性），发现冲突提示 `daemon --once` 对账，doctor 不自动转移状态。 |
| 13| [`docs/usecases`](../usecases) | 路径别名软链接 | 指向 `docs/usercases`，保障跨文档与 CLI 引用的绝对兼容性。 |

---

## 3. PRD v2.5 权威架构裁定（D-1 ～ D-9）落地对照表

> 裁定编号与定义严格对齐权威提案源 [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) §2（L34–L42）：

| 权威裁定编号与核心原则 | 用例体系落地位置 | 详细设计与机制保证 |
|---|---|---|
| **D-1: vote_result.json 不可变单写，DEADLOCK 即时写盘并 HOLD** | UC-5 §2.c/d, UC-7 §2.d, UC-9 §2.d | 当计票出现 DEADLOCK 时，Orchestrator 即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）并进入 HOLD；任何人工接管操作均不得修改或覆盖 `vote_result.json`。机器决策严格收敛为 `APPROVED`、`REWORK_REQUIRED`、`DEADLOCK` 三态。 |
| **D-2: 独立 review_disposition 产物** | UC-6 全文, UC-1 h0(2), README 产物表 | 执行者收到 Type E `DISPOSITION_REQUIRED` 后在 `.macao/.dispositions/r<round>/executor.disposition.yml` 编写独立处置产物；三态（`DRAFT`/`PENDING_ADMIN`/`FINAL`）；提供 100% 覆盖率，`FINAL` 严禁遗留 `NEEDS_ADMIN`。 |
| **D-3: Reviewer 显式 ABSTAIN 机制** | UC-4 §3.A2, UC-5 §2.b, UC-9 §2.a/c | 显式区分 `source: "manifest"` 与 `source: "timeout"`；ABSTAIN 计入 `accounted` 席位以触发 E3，但**严格排除在非弃权有效集合 $E_N, E_W$ 之外**。 |
| **D-4: BACKLOG 命名更名为 DEFERRED** | UC-6 §2.b, UC-1 h0(2), PRD §2.5 | 统一处置枚举为 `ADOPTED / DEFERRED / REJECTED / NEEDS_ADMIN / EXEMPTED_BY_ADMIN`，`DEFERRED` 必须附带延期 rationale，`requires_new_checkpoint=false`。 |
| **D-5: requires_new_checkpoint 显式布尔守卫** | UC-6 §2.b/c, UC-3 §2.g | 每项 issue 必须提供非空布尔值 `requires_new_checkpoint`；全 false 且 APPROVED $\implies$ E4 进入 `MERGING`；任一 true $\implies$ E5a 进入 `REWORK`；严禁编排器从文本推测。 |
| **D-6: 纯整数加权五重门禁与独裁帽** | UC-5 §2.b, UC-1 h0(3), UC-10 §2.b | 统一采用纯整数四则运算：$\forall i, 3w_i < 2W$、$E_N \ge \lceil 2N/3 \rceil$、$E_W \ge \lceil 2W/3 \rceil$、$3W_{win} \ge 2E_W$、胜方席位 $\ge 2$；严禁浮点数运算与静默四舍五入。 |
| **D-7: FSM 三投影与 E1～E10 转移一致** | UC-4 §2.g, UC-5 §2.a/d, UC-6 §2.c, UC-7 §2.c | Layer 1a 仅在全席位 accounted（`accounted == configured`）时触发 E3；Layer 1c 按 `requires_new_checkpoint` 与 `decision` 精确分流 E4（MERGING）与 E5a（REWORK）。 |
| **D-8: Git Evidence Ref 体系与两阶段 Push 校验** | UC-3 §2.c, UC-4 §2.b, UC-8 §2.关卡1/6 | 证据进入独立 `refs/macao/evidence/<task_id>/r<round>`；AEP/1.1 零 base64（通过 `{path, evidence_commit, sha256}` 引用，≤16 KiB 字节预算）；UC-8 关卡 1 强制 Pre-merge `ls-remote` 校验已推送。 |
| **D-9: init / doctor / reconcile / adopt 职责边界与单写者垄断规范** | UC-1, UC-10, README 产物表 | 静态配置（Admin 单写）、开发检查点（Executor 单写）、评审意见（Reviewer 单写）、共识计票（Orchestrator 单写）、意见处置（Executor 单写）、人工接管（Admin 单写）。 |

---

## 4. 自动化可复现验证结果

为确保全量用例文档无格式瑕疵、无非法控制字符且与机器代码契约 100% 互锁，已执行全套自动化验证：

1. **全用例文档控制字符字节扫描**：
   - 扫描范围：`docs/usercases/*.md`（全部 13 份文档）
   - 结果：**全部 13 份文档 0 控制字符（100% CLEAN）**。
2. **用例内嵌 YAML/JSON 示例契约校验**：
   - `UC6-issue-triage-rework.md` 处置示例 $\rightarrow$ `review_disposition.schema.json`：**PASS**
   - `UC3-dev-checkpoint.md` `.dev.yml` 示例 $\rightarrow$ `dev_manifest.schema.json`：**PASS**
   - `UC1-init-gemini.md` `macao.yaml` 规格示例 $\rightarrow$ `macao_config.schema.json`：**PASS**
3. **Draft-07 Schema 与 Fixture 双向校验**：
   - `docs/schemas/fixtures/valid/` 8 份正例 fixture：**8/8 PASS**
   - `docs/schemas/fixtures/invalid/` 7 份反例 fixture（含 `admin_override_invalid_choice.json`、`disposition_final_with_needs_admin.yml`、`vote_result_cancelled_decision.json` 等）：**100% 准确拦截（FAIL-CLOSED）**
   - `docs/schemas/` 与 `src/macao/schemas/` 8 份同名契约：**0 diff，逐字节完全一致**。
4. **全流程与回归测试套件**：
   - 测试执行：`PYTHONPATH=src python3 -m unittest discover tests`
   - 结果：**Ran 86 tests — 100% OK（86/86 PASS，0 Failures，0 Errors）**。
5. **Python 代码静态编译**：
   - `python3 -m compileall -q src tests`：**0 Errors**。

---

## 5. 专家委员会独立评审指引

请评审专家（Claude、Codex、GLM、Qwen、Grok）依据 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) 进行独立交叉核验：

1. **反例库场景穷尽性验证（GUIDELINES §6）**：
   - 核验各用例对非法输入（如：缺 `signal: EXPLICIT`、未拓扑前进的 commit、遗漏 issue 的 disposition、`FINAL` 状态包含 `NEEDS_ADMIN`、非法 `choice`、未推送 evidence ref 等）的 fail-closed 拦截行为是否明确；
2. **三层载体与零语义创作原则**：
   - 核验 AEP/1.1 与 agmsg ping 是否完全剥离了长正文生成，是否严格遵循 16 KiB 字节预算与 Evidence Ref 指针机制；
3. **单写者垄断与不可变性**：
   - 核验 `vote_result.json`、`admin_override.json`、`executor.disposition.yml` 的写者边界是否在全量用例中保持绝对互斥，严禁任何二次回写或状态伪造。

---

## 6. 申请定级建议

综上所述，MACAO 全量用例体系已与 PRD v2.5 规格及 D-1～D-9 权威架构裁定达成高度一致，全部前序阻断项均已实质闭环，具备严密的逻辑自洽性与机器可验证性。

建议专家委员会正式授予 **L1 DOC-ALIGNED / PG-0** 准入认证，批准全量用例体系作为 Phase 1~5 研发实施与测试验收的官方操作基准。
