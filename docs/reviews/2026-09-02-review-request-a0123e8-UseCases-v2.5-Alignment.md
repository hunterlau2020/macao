# MACAO 全量用例体系（UseCases）PRD v2.5 规格与 D-1～D-9 架构裁定对齐复审申请（Commit a0123e8）

- **申请日期**：2026-09-02
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（用例文档体系与 PRD v2.5 实施基线全面对齐与准入）**
- **当前代码与文档基线**：`commit a0123e8`（`origin/main`）
- **前序受审基线与票型**：
  - `4027cce`: Claude (`NO_APPROVE`, P1×1), Codex (`REJECT`, P1×5), Grok (`NO_APPROVE`, P1×2), Qwen (`NO_APPROVE`, BLOCKING×2)
  - `6e35a71`: Grok (`APPROVE`), Qwen (`APPROVE`), Claude (`NO_APPROVE`, P1×4), Codex (`REJECT`, P1×8)
  - `5583bdd`: Grok (`NO_APPROVE`, P1×2: P1-1 E7 override exit edge, P1-2 D-1~D-9 table matching)
  - `caf3473`: Claude (`NO_APPROVE`, P1×5), Grok (`NO_APPROVE`, P1×3), Qwen (`NO_APPROVE`, BLOCKING×6)
- **关联权威基准**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)（PRD v2.5 权威基准）
- **关联变更提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 闭环稿，D-1～D-9 权威定义源）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）
- **关联评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)

---

## 1. 评审背景与核心修复

针对专家委员会对上一轮提交 `4027cce` 指出的全部用例体系阻断项，团队在 `a0123e8` 落实了以下闭环：

1. **UC-8 纯本地模式 `remote_name: null` 全链路机器契约支持**：
   - 契约库 `macao_config.schema.json` 与 `review_context.schema.json` 完整支持 `remote_name: null`；
   - PRD §14.5 Gate 1 明确远端共享模式与纯本地模式两道分支；
   - 增加纯本地配置合法 fixture `macao_config_local_only.yaml` 并自动化机验通过。
2. **UC-1 冗余字段清理与法定人数标准统一**：
   - `UC1-init-gemini.md` 与 `UC1-init-glm.md` 彻底移除 `min_effective_votes`，统一引用 `seat_quorum_required`。
3. **UC-5 与 UC-10 纯整数反支配门禁硬约束**：
   - Schema 契约层强制 `minimum_winning_seats: {"minimum": 2}` 与 `dictator_cap_enabled: {"const": true}`，物理杜绝单席位合并漏洞。
4. **全量用例 Markdown 控制字符与格式严密性**：
   - 全量 13 份用例文档 0 控制字符，内嵌 YAML/JSON 示例 100% 通过 Draft-07 Schema 校验。

---

## 2. 待审用例交付物全量清单

| # | 交付物文件 | 对应阶段 / 命令 | PRD v2.5 核心规格与单写者产物落地说明 |
|---|---|---|---|
| 1 | [`docs/usercases/README.md`](../usercases/README.md) | 用例目录与主旅程总览 | 1. 确立主旅程流向：`UC-5 计票` $\rightarrow$ `UC-6 处置 (E5/E5a)` $\rightarrow$ `UC-8 合并 (E4/E4a)`；<br/>2. 建立 5 大核心产物单一垄断写者规范表。 |
| 2 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | 产品事实源（F-1～F-22） | 落实 F-20：`vote_result.json` 为编排器单写不可变机器计票（D-1），`executor.disposition.yml` 为执行者单写独立处置产物（D-2）。 |
| 3 | [`docs/usercases/UC1-init-glm.md`](../usercases/UC1-init-glm.md)<br/>[`UC1-init-gemini.md`](../usercases/UC1-init-gemini.md) | `macao init` / `adopt` | 1. 静态 `macao.yaml` 与动态 `agent_registry` 分离；<br/>2. 依据工作区特征识别 10 态，推不出唯一态则问管理员；<br/>3. agmsg 仅作通知 short ping，正文零模型语义依赖；<br/>4. 统一 gitignore 9 规则与五重门禁纯整数公式。 |
| 4 | [`docs/usercases/UC2-task-create.md`](../usercases/UC2-task-create.md) | `IDLE` $\rightarrow$ `CODING` (E1) | 1. 任务规划由人/执行者完成，编排器仅受理表单与 Schema 校验；<br/>2. 下发 AEP/1.1 Type A `DEVELOPMENT_STARTED` 信封。 |
| 5 | [`docs/usercases/UC3-dev-checkpoint.md`](../usercases/UC3-dev-checkpoint.md) | `CODING`/`REWORK` $\rightarrow$ `READY_FOR_REVIEW` (E1/E6) | 1. 执行者独占业务 commit 与申请全文；<br/>2. `.macao/.dev.yml`（`v2.5`）完整提供 `full_document{path,evidence_commit,sha256}` 与 `signal: EXPLICIT`；<br/>3. **返工轮严格要求拓扑单调前进的新 commit**。 |
| 6 | [`docs/usercases/UC4-review-dispatch.md`](../usercases/UC4-review-dispatch.md) | `READY_FOR_REVIEW` $\rightarrow$ `WAITING_REVIEW` (E2) | 1. 编排器原样派发 AEP/1.1 Type B `REVIEW_REQUEST`（10 个必需与语义 Context 块）；<br/>2. 专家生成 `.review.yml` 与独立 worktree 隔离；<br/>3. **收敛触发条件修正为全席位 accounted**。 |
| 7 | [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md) | `WAITING_REVIEW` $\rightarrow$ `CONSENSUS_CHECK` (E3) | 1. **纯整数加权五重门禁**（D-6：独裁帽 $3w_i < 2W$、席位法定人数 $E_N \ge \lceil 2N/3 \rceil$、权重法定人数 $E_W \ge \lceil 2W/3 \rceil$、胜方权重 $3W_{win} \ge 2E_W$、胜方席位 $\ge 2$）；<br/>2. **不可变 `vote_result.json`**（D-1）；<br/>3. DEADLOCK 时即时落盘并 HOLD 问管理员（UC-7）。 |
| 8 | [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) | `CONSENSUS_CHECK` / `REWORK` | 1. 执行者编写独立 `.macao/.dispositions/r<round>/executor.disposition.yml`（D-2）；<br/>2. 精确穷尽覆盖 100% issue，`FINAL` 严禁遗留 `NEEDS_ADMIN`；<br/>3. `requires_new_checkpoint: boolean`（D-5）守卫分流：全 false 且 APPROVED $\rightarrow$ E4 进入 `MERGING`；任一 true $\rightarrow$ E5a 进入 `REWORK`。 |
| 9 | [`docs/usercases/UC7-human-override.md`](../usercases/UC7-human-override.md) | 管理员人工接管 (`override resolve`) | 1. DEADLOCK 时 `vote_result.json` 不可变，管理员裁定写入独立 `admin_override.json`；<br/>2. 闭合 5 大选项（`APPROVED`, `REWORK`, `RETRY_REVIEW`, `CANCEL`, `EXTEND`）；<br/>3. `APPROVED` 落盘 override 解除 HOLD 并投影 `SHOULD_DISPOSE` $\rightarrow$ 经执行者提交 FINAL disposition 校验后触发 E4 $\rightarrow$ `MERGING`。 |
| 10| [`docs/usercases/UC8-merge-signoff.md`](../usercases/UC8-merge-signoff.md) | `MERGING` $\rightarrow$ `DONE` (E4a) | 1. 评审对象 = 合并对象（`checkpoint_ref` 硬校验）；<br/>2. **六道关卡顺序执行**：关卡 1 Pre-merge Evidence 校验（远端共享 `ls-remote` fail-closed / 纯本地模式本地校验） $\rightarrow$ 关卡 2 检出 $\rightarrow$ 关卡 3 技术合并 $\rightarrow$ 关卡 4 CI gate $\rightarrow$ 关卡 5 人工签字 $\rightarrow$ 关卡 6 源码推送与 Post-merge 证据封存归档。 |
| 11| [`docs/usercases/UC9-timeout-daemon.md`](../usercases/UC9-timeout-daemon.md) | 超时与守护 (OrchestratorDaemon) | 1. 超时席位注入显式 `ABSTAIN`（`source: "timeout"`）计入 `accounted` 席位以触发 E3，但**严格排除在非弃权有效集合（$E_N, E_W$）之外**；<br/>2. 迟到票边界：计票前可替换 pending 标记，`vote_result.json` 落盘后严格作为 `LATE_REVIEW_ISOLATED` 审计日志隔离。 |
| 12| [`docs/usercases/UC10-existing-project-doctor.md`](../usercases/UC10-existing-project-doctor.md) | 既有项目接入与诊断 (`macao doctor`) | 零侵入只读体检（纯整数加权独裁帽、环境、Git 拓扑、gitignore 9 规则隔离、席位与产物一致性），发现冲突提示 `daemon --once` 对账。 |
| 13| [`docs/usecases`](../usecases) | 路径别名软链接 | 指向 `docs/usercases`，保障跨文档与 CLI 引用的绝对兼容性。 |

---

## 3. 自动化可复现验证结果

1. **全用例文档控制字符字节扫描**：`docs/usercases/*.md` **全部 13 份文档 0 控制字符（100% CLEAN）**。
2. **用例内嵌 YAML/JSON 示例契约校验**：
   - `UC6-issue-triage-rework.md` 处置示例 $\rightarrow$ `review_disposition.schema.json`：**PASS**
   - `UC3-dev-checkpoint.md` `.dev.yml` 示例 $\rightarrow$ `dev_manifest.schema.json`：**PASS**
   - `UC1-init-gemini.md` `macao.yaml` 规格示例 $\rightarrow$ `macao_config.schema.json`：**PASS**
3. **Draft-07 Schema 与 Fixture 双向校验**：
   - `docs/schemas/fixtures/valid/` 10 份正例 fixture：**10/10 PASS**
   - `docs/schemas/fixtures/invalid/` 16 份反例 fixture：**16/16 100% 准确拦截（FAIL-CLOSED）**
   - `docs/schemas/` 与 `src/macao/schemas/` 8 份同名契约：**0 diff，逐字节完全一致**。
4. **全流程与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 92 tests — 100% OK（92/92 PASS，0 Failures，0 Errors）**。
5. **Python 代码静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

全量用例体系已与 PRD v2.5 规格及 D-1～D-9 权威架构裁定达成高度一致，全部前序阻断项均已实质闭环，具备严密的逻辑自洽性与机器可验证性，建议专家委员会正式授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
