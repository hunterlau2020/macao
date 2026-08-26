# MACAO docs/（PRD v2.2 及配套文档）对齐/评审结论

- **评审日期**：2026-08-26
- **评审对象**：commit `8ab9be7`（PRD v2.2 修订版，含 `docs/schemas/`、`docs/README.md`）下 `docs/` 全部文档
- **评审范围**：跨文档对齐（README / EXECUTIVE_SUMMARY / IMPROVEMENT_SUMMARY / SRSv1 横幅 / schemas+fixtures / STATUS）+ PRD 内部一致性（SPEC）；上轮 684a012 三份评审 P0/P1 闭环验证
- **对齐基准**：`MACAO_PRD_v2.md`（v2.2，权威基准）；方法依据 `MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11
- **证据类型**：DOC/SPEC（全部给出路径+行号）+ 机器校验（jsonschema 4.x + PyYAML，脚本重放，19 项检查 2 项 FAIL，见附录）
- **结论**：**未达 L1 DOC-ALIGNED，维持 PENDING_REVIEW / 不授予 PG-0**。理由：4 个 P1 属文档内部矛盾或契约缺口（违反 L1 最低条件"交叉引用不矛盾"）。上轮 P0（F1/F2）与多数 P1 已确认修复到位。

---

## 已对齐 / 已确认项

| # | 项 | 证据 | 状态 |
|---|----|------|------|
| 1 | 上轮 F1（MERGING 中间态）已修复 | PRD §3.3 E4/E4a/E4b（L795-797）、§14.5 合并流水线、§3.4 推演同步（L830-834） | VERIFIED (DOC) |
| 2 | 上轮 F2（Reviewer 执行权限边界）已修复 | PRD §12.2 execution_mode 强制规则（L1330-1333）、§12.3 矩阵补列（L1337-1341）、§5.3 worktree 注入（L1004-1006）、§15.3 风险表（L1486） | VERIFIED (DOC) |
| 3 | 上轮 codex P1-1/2/3、claude F3~F6、gemini 环节 1/2/3/5/6 均已落文 | repository 统一（§2.4 注 L536）、Task Schema（§14.1 L1429 + Type A）、DDL/Reconcile（§11.4/11.5）、signoff（§13/§14.5）、输出自愈（§12.5）、PTY 规范（§12.6）、DLQ（§11.6）、rebase 策略（§14.5 步 1） | VERIFIED (DOC) |
| 4 | PRD "下述 JSON 示例均为合法 JSON" 声明 | 机器校验：8/8 JSON 块 parse 通过；7 个 AEP 示例全部通过 `aep_envelope.schema.json`；vote_result 示例通过其 Schema | VERIFIED (SIM) |
| 5 | PRD 产物 YAML 示例与 Schema 一致 | §2.1 `.dev.yml`、§2.2 `.review.yml` 示例通过对应 Schema；§13 `macao.yaml` 示例通过 config Schema；字段嵌套路径（quality_metrics/git 在 development 之下）与 §2.1 伪代码读取路径一致（上轮盲点 A 未复发） | VERIFIED (SIM) |
| 6 | fixtures 行为正确 | valid 3 例全过、invalid（status↔vote 冲突）被正确拒绝；if/then 形式化与 PRD §2.2 映射表一致 | VERIFIED (SIM) |
| 7 | 共识决策表覆盖 Guidelines §6 场景库投票类场景 | PRD §2.3 决策表（L400-409）含全同意/1:1/弃权/全超时；§6.2 降级路径与之一致 | VERIFIED (DOC) |
| 8 | 文档治理 | SRSv1 历史横幅准确；STATUS.md 撤回过早的 L1 定级（符合"真理不等于投票"）；README 索引与文档体系一致 | VERIFIED (DOC) |

## P0：必须先解决

（无）

## P1：发布/进入下一阶段前应修正

**P1-1 §6.1 触发条件 1 与分层承诺矛盾（Layer 2 被赋予置信度阈值）**
- PRD L1046-1050：`State ambiguity: "Layer 1 signal missing AND Layer 2 confidence < 0.7"`，timeout 字段为 HOLD 语义。
- 矛盾点：§3.1（L684-697）与 §3.2 伪代码（L753-757）明确 Layer 2 **仅日志/预警、固定 confidence=0.8、永不触发转移**；`< 0.7` 是 **Layer 3** 的诊断置信度阈值（§3.1 L697、§3.2 L765、E8 L801）。EXEC L228 的简化表述反而与 v2.1 语义一致，说明 §6.1 该行是陈旧文案。
- 风险：实现者据 §6.1 给 Layer 2 实现阈值触发 override，破坏"仅 Layer 1 产生业务状态转移"的行为约定（§3.2 L777-781）。
- 修复建议：条件改为 "Layer 1 信号缺失/无效 且（经 Layer 3 诊断置信度 < 0.7 或满足 E8）"，与 E8 统一。

**P1-2 §1.1/§1.2 与 §3.3 九态 FSM 不同步（MERGING 缺失），README 传播错误**
- §3.3（L804）定义 9 态含 `MERGING`；§1.1 图（L100-112）APPROVED 直接 "Merge/Done"，无 MERGING；`CHANGES_REQUEST → Loop back to PHASE 1`（L111）与 E5 目标态 `REWORK` 不符（REWORK ≠ CODING/PHASE 1）。
- §1.2（L117 自称与 §3.3 "一一对应"）MERGE/REWORK 行（L126）主状态仅 `DONE`/`REWORK`，无 `MERGING`；CONSENSUS 行离开条件只写 E4/E5（L125），漏 E7。
- README.md L24 "工作流 FSM 与统一转移表：§1.1 / §3.3（含 MERGING 合并中间态）"——暗示 §1.1 含 MERGING，实际没有。
- 风险：以 §1.1/§1.2 为实现入口的读者会遗漏 MERGING 状态与 E4b 回退。

**P1-3 review_context 质量块双命名（quality_snapshot vs quality_metrics），两节字段集不一致**
- §2.4 Type B（L508-513）：`quality_metrics: {tests_passed, test_count, coverage, lint_score}`，另有 `dev_checkpoint`/`repository`。
- §5.2（L952-963）：`quality_snapshot: {tests{...}, static_analysis, performance}`，另有 `executor_self_assessment`/`history`/`references`（Type B 示例均无）。
- §5.2 注（L1033）只说"允许省略可选字段"，未裁决**命名冲突**（quality_snapshot vs quality_metrics）与**权威字段全集**；review_context 无独立 JSON Schema（schemas/ 仅有信封，payload 为自由 object）。
- 违反 Guidelines §5"唯一权威表"原则；§12.4 Adapter Conformance 缺少可执行的 context 契约。

**P1-4 Deadlock/人工裁定路径与 vote_result Schema、Layer 1c else 分支、E7 的衔接缺口**
- `vote_result.schema.json` L51：decision 枚举仅 `APPROVED | REWORK_REQUIRED`；而 §3.3 超时行（L794）"弃权票记入 vote_result.json"、§1.2 CONSENSUS 行（L125）要求先写出 vote_result——Deadlock 轮的 decision 值无法表达。
- §3.2 Layer 1c（L750-751）：`DONE if decision == 'APPROVED' else REWORK`——二值 else 会把任何非 APPROVED 决策静默映射为 REWORK，与 E7"Deadlock 人工裁定"（L800）冲突；若 Deadlock 轮不写 vote_result 则 FSM 停在 CONSENSUS_CHECK（该行为或正确但文档未写明）。
- 人工裁定选项三处枚举不一致：Type G `options: [APPROVED, REWORK, RETRY_REVIEW]`（L658）vs §14.1 `--choice APPROVED|REWORK|RETRY|CANCEL`（L1434）vs E7 目标 `DONE / REWORK / 终止`（L800）。`RETRY/RETRY_REVIEW` 无对应转移定义；`终止/CANCEL` 无 FSM 终态（9 态不含 CANCELLED，§14.2 cancel L1442 无状态落点）。
- 违反 Guidelines §6"每个场景可唯一推出预期结果"要求（Deadlock 轮的 vote_result 内容与状态出口目前不可唯一推导）。

## P2/P3：可延期但需登记

**P2-1 Type D 示例 round 值与自身规则矛盾**：Type D（L584）`"round": 1`；§3.2（L718）"发送 REWORK_REQUEST 时 +1"、场景推演二步骤 6（L842）round=2。示例应改为 2 或明确 round 字段语义（"被评审轮" vs "即将开始的返工轮"）。

**P2-2 EXECUTIVE_SUMMARY 产物示例未通过 Schema（机器校验 FAIL ×2）**：
- `.dev.yml` 示例（EXEC L124-151）缺必填 `review_round`；`quality_metrics.coverage` 应为 `test_coverage`（PRD §2.1 L169 / dev schema）。
- `.review.yml` 示例（EXEC L157-174）缺必填 `version`/`checkpoint_ref`/`review_round`；`feedback` 为数组，PRD §2.2 为对象（summary/severity_breakdown/categories）。
- 另：架构速写（EXEC L76-90）模块名（Agent Registry/State Engine/Workflow Controller）与 §11.1 组件清单不一致；"评审效率 ↑ 500%"（EXEC L42）无出处且不在 L70 目标值注释覆盖范围内。
- Guidelines §5 明确禁止摘要示例字段名与权威 Schema 不一致；至少应加"示意，不通过 Schema 校验"的显著标注。

**P2-3 fixtures 覆盖面与宣称不符**：`schemas/README.md` L17 表述覆盖"正反 fixtures"为全部五类契约的强制输入；实际 invalid 仅 1 例（review status↔vote），dev/vote_result 无反例（如缺 signal、tests_passed=false 且无 exempt、decision 越界），AEP 信封与 macao.yaml 无正例。E4b/E8 新路径无 fixture。建议补齐后再宣称。

**P2-4 人工接管请求自身超时未定义**：Type G payload 含 `deadline`（L659）、§6.1 trigger 3 timeout "10 minutes"（L1062）到期后系统动作未定义（仅 trigger 1 定义了 HOLD 语义 L1050）。Guidelines §6 场景库明确要求"人工接管超时后系统的默认动作"可唯一推导——当前不可推导。建议统一为"HOLD + 持续告警，永不静默推进"。

**P3-1** KPI "Explicit Signal Usage Rate >99% = 状态转换由 .yml 驱动的比例"（L1146）与 §3.3 命令型+产物型双来源模型矛盾；分母应排除命令型转移（E1/E2/E4a/E7）。
**P3-2** `timeouts.development: 2h`（L1401）与 E8 的 60min 无进展（L801）关系未说明；`checkpoint_validation: 1m` 超时后的处置未定义。
**P3-3** δ2 称 STATE_CHANGED 附 content_base64（L1590），Type F 示例（L634-639）未体现该字段。
**P3-4** PRD 一级标题仍为 "产品方案 v2.0"（L1），版本历史已至 v2.2；EXEC/README 均称 v2.2。
**P3-5** §12.2 `full` 模式"仅允许 Executor 在其任务工作区内使用"（L1332）缺强制机制说明（Reviewer 有 worktree+sandbox，Executor 侧无对应机制描述）。
**P3-6** §5.3 Step 5 写 `.macao/.reviews/reviewer_id.review.yml`（L1023）占位符未替换为 `<reviewer_id>`。

## 交叉文档需做的文字修订

1. README.md L24：改为"§3.3（含 MERGING；§1.1/§1.2 为简化视图，以 §3.3 为准）"或在 P1-2 修复后保持。
2. EXECUTIVE_SUMMARY：按 P2-2 修正两示例字段名/结构，补 `review_round`/`checkpoint_ref`；"↑500%"标注目标值或删除；架构速写对齐 §11.1。
3. STATUS.md：登记本轮 4×P1 / 4×P2 / 6×P3 及处理位置（本轮评审仅出报告，未代改）。
4. schemas/README.md：fixtures 覆盖表述与实际对齐（或补齐 fixtures）。

## 建议的闭环顺序与验收标准

1. **先修 P1-1/P1-2**（纯文字同步，无语义争议）→ 验收：§1.1/§1.2/§6.1 与 §3.3/E8 逐行对照无矛盾；
2. **P1-3**：在 §2.4 或 §5.2 二选一定名（建议 quality_metrics，与 .dev.yml 一致），给出 review_context 字段全集表；验收：两节示例字段可逐一对映；后续可为 review_context 增补 JSON Schema + fixtures；
3. **P1-4**：明确 Deadlock 轮 vote_result 写出时机与 decision 表达（建议枚举扩展 `DEADLOCK_RESOLVED` 或约定"先人工裁定、后写终局 decision"+ Layer 1c 改为显式三分支）；统一 override 选项枚举并补 RETRY_REVIEW/CANCEL 的转移与终态；验收：Deadlock 场景从 E3 起每一步可唯一推导（SIM 复核）；
4. P2-2/P2-3 随下一版一并处理；全部 P1 关闭后申请 L1 复审定级（PG-0）。

## Reviewer 自审记录

- 按 Guidelines §9 五项自检执行：字段名 vs 读取路径（PRD 内已核，EXEC 存在不一致已列 P2-2）；确定性用语（99%/100% 各处均有目标值标注，EXEC "500%" 除外已列）；YAML/JSON 代码块可解析性（机器校验 19 项，PRD 全过、EXEC 2 项 FAIL）；每项 P1/P2 均附路径+行号。
- 本评审未覆盖：IMPROVEMENT_SUMMARY 历史叙事数字（如投票通过概率 33%/89%/75%）的出处核查——属历史记录性质，未列为问题。
- 利益声明：无。

---

### 附录：机器校验脚本结果（摘要）

```
PASS  fixture valid/dev.yml / review.yml / vote_result.json -> 对应 Schema
PASS  fixture invalid/review_status_vote_conflict.yml 被正确拒绝
PASS  PRD 8/8 JSON 块解析；7 AEP 示例过信封 Schema；vote_result 示例过 Schema
PASS  PRD 5/5 YAML 块解析；.dev.yml/.review.yml/macao.yaml 示例过对应 Schema
FAIL  EXEC yaml #1（.dev.yml 示例）：缺 required 'review_round'
FAIL  EXEC yaml #2（.review.yml 示例）：缺 required 'version'（另缺 checkpoint_ref/review_round）
19 checks, 2 failed
```

（脚本：jsonschema + PyYAML 逐块提取校验，可复现；HEAD = 8ab9be78）
