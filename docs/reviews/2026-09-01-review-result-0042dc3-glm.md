# PRD 修改提案 v2.5（`docs/PRD_CHANGE_PROPOSAL_v2.5.md`）评审结论

- **评审日期**：2026-09-01
- **评审对象**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md`（DRAFT，commit `0042dc3`）
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.4、`docs/usercases/PRODUCT-FACTS.md`（F-1~F-16 + 第三节裁定）、`docs/usercases/UC1–UC10`、现行 Schema/代码/测试、`docs/MACAO_REVIEW_GUIDELINES.md`
- **评审人**：glm（独立评审，逐项机验取证）
- **结论**：**不建议原样批准（NOT-ACCEPTED）**。提案方向正确、解决了真实缺陷（evidence ref 分离、AEP 字节预算、disposition 闭环、加权治理、动态接管），但存在 **1 项 P0**（未显式声明地推翻已裁定 fact F-13/F-16，与三天内刚对账修复的 UC-1/5/6 直接冲突）和 **2 项 P1**。P0/P1 修订后可复审；架构主体（§4/§5/§7）予以肯定。

---

## 已对齐 / 已确认项

| 提案内容 | 判定依据 |
|---|---|
| P-1 编排器零语义创作 | F-9~F-12 ✅；正/反清单可机器审计 |
| §4.1 权威产物表（8 产物，写者/含长正文逐项闭合） | F-14/F-15 ✅；每行写者与内容职责一一对应 |
| §4.2 `review_context` 引用集合 + 失败关闭四条件 | F-8/F-14 ✅；解决 GUIDELINES §4"字段名 vs 读取载体"类问题 |
| §4.4 evidence ref 与 `checkpoint_ref` 分离 | **本提案最高价值项**：修复现行缺陷——PRD:833/859/1510 的"`.review.yml` 纳入 git 提交/归档随 git 提交"确实会移动 source HEAD、破坏"评审对象=合并对象"（PRD §14.5 硬约束）。分离后既保留 docs/reviews/ 的 Git 历史又不触发未评审新 commit，论证成立 |
| §5 init 三模块 + 判定优先级 + AI diagnostic_only | F-1/F-2/F-6/F-12 ✅；5.2 优先级与 UC-1 h3"Layer 1 唯一/旁证不覆盖"一致；`--yes` 歧义 fail-closed 与 UC-1 A7 一致 |
| §5.4 单一 FSM + 只读投影 | F-4 ✅；不引入第十一态 |
| §6 加权规则（快照冻结、权重治理、默认全 1） | F-16 ✅；6.3"校准证据先行"甚至严于 F-16 要求 |
| §7 三层审计六元组关联 | F-7 ✅；可测（§9.3-12） |
| 代码块可解析性（§3.3 YAML、§3.4 JSON、§4.2/§6.1 YAML） | 逐块目验：无非法注释、字段名与自述 Schema 一致 ✅（GUIDELINES §9-D） |

## P0：必须先解决

### P0-1　提案未显式声明地推翻 F-13/F-16，与刚完成对账的 UC-1/UC-5/UC-6 直接冲突

- **证据（提案）**：§3.4"`issues_index`…不得出现『是否采纳』。采纳信息只在 `review_disposition` 中"；P-3"`vote_result.json` 是不可变的机器裁决记录…『哪些意见采纳』写入独立的 `review_disposition` 产物"。
- **证据（fact）**：PRODUCT-FACTS F-13"把问题或建议的标题清单、正文索引、发现该问题的专家、严重性、**是否采纳写入 `vote_result`**"；F-16"单条意见是否采纳仍由执行者**在汇总段**标明"；三节裁定"总结采纳…由执行者**写入 `vote_result` 汇总段**"。
- **证据（下游已对齐）**：`UC1-init-glm.md:96/104`、`UC5-consensus-tally.md:45/82/91-92`、`UC6-issue-triage-rework.md:7/25`（commit `2cd45ed`，2026-09-01 刚按 F-13 修复完 P1-1/P1-2）。
- **矛盾点**：提案把采纳处置从"vote_result 内执行者汇总段（`issues_summary`）"改为"独立 `review_disposition` 产物 + vote_result 完全不可变"。这**可以**是更优的工程决策（单一写者、不可变性更强、覆盖 APPROVED 无返工场景），但它是**对已裁定 fact 的结构性推翻**：按 GUIDELINES §8，"审计相关的结构性变更（产物路径、状态枚举、投票公式）应要求多 reviewer 共识而非简单多数"，且提案自我声明"输入：PRODUCT-FACTS F-1~F-16"却未在 §10（需管理员裁定事项）或 §11 中点名这一推翻。
- **最低修正**：§10 增加显式裁定项："是否推翻 F-13/F-16 的『采纳写入 vote_result 汇总段』方案，改为独立 `review_disposition`"；若裁定通过，§11 迁移清单必须包含"修订 PRODUCT-FACTS（F-13/F-16 标注 SUPERSEDED-BY-v2.5）+ 回改 UC-1 h0(2)/UC-5 §2c/UC-6 b"，否则文档体系将第三次在同一问题上分裂（UC-1 旧稿 → F-13 修复 → 提案再反转）。

## P1：批准前应修正

### P1-1　"ABSTAIN 仅由超时降级生成"与现行已实现行为冲突，迁移路径缺失

- **证据（提案）**：§3.1"机器票：`YES_APPROVE`、`NO_APPROVE`；`ABSTAIN` 仍只由超时降级流程生成"。
- **证据（现状）**：该口径确实来自 PRD v2.4 §2.2（PRD:305/318"Reviewer 无弃权通道"），**但**现行 `docs/schemas/review_manifest.schema.json:26/59/75`（`ABSTAIN` 枚举 + `ABSTAINED↔ABSTAIN` 互锁）、`live_dispatcher.py` 调和逻辑、`test_review_extractor_supports_abstain`（test_phase3.py:285）与 UC-4 A2（"专家明确弃权 = 合法票"）均为 Commit `ac32dbb`（2026-08-31）刚闭环的三值支持。
- **要求**：提案必须在 §8/§9 显式裁决：要么回滚 Schema/代码/测试至二值（列出迁移与回归项），要么修订 PRD §2.2 承认显式弃权通道（并说明弃权与超时弃权在计票中的同构性）。现状是"提案沿用 PRD 旧文、无视已实现行为"，实现者无从执行。

### P1-2　§8 修改清单遗漏现行"产物随 git 提交"语义的迁移项

- **证据**：提案 §8.1 覆盖 §1.2/§2.x/§3.4/§6/§11/§14/§16，但未列：PRD:833（E3 伴随动作"`.review.yml` 纳入 git 提交"）、PRD:416（§2.2 写入约定同义）、PRD:859（§3.4 生命周期表）、PRD:1510（§14.1 第 7 步"归档…并随 git 提交"）。这四处正是 §4.4 evidence ref 要替换的旧语义；不列入清单将导致 E3 实现仍向 source branch 提交、与 §4.4 直接打架。
- **要求**：§8.1 增行"§2.2 写入约定 / §3.3 E3 伴随动作 / §3.4 生命周期表 / §14.1-7：产物 git 提交语义整体迁移到 evidence ref"。

## P2/P3：可延期但需登记

- **P2-1**　处置穷尽性放宽未声明：UC-6 d2 要求清单穷尽**全部** issue；提案 §3.3 规则只强制覆盖 BLOCKING（REWORK 轮）与 ADVISORY（APPROVED 轮），非阻断意见在 REWORK 轮可被静默忽略。若为有意放宽（降低执行者负担），应在 §3.3 注明并与 UC-6 对账；否则恢复穷尽性。
- **P2-2**　`role_projection`（§5.4：WAITING/ACTION_REQUIRED/WORKING/RESPONDED/NOT_APPLICABLE）与 UC-1 h2 `role_view`（AWAIT_TASK/SHOULD_CODE/…）构成第三套术语。按 GUIDELINES §5 唯一权威表要求，须给出两套枚举的映射表并择一为规范名。
- **P2-3**　独裁帽替代关系未说明：UC-1 h0(3)/UC-5 的"任一席位权重 < 2/3 Σweight 启动校验"在提案中由 `weight_quorum ≥ ceil(2W/3)` + `minimum_winning_seats` 事实覆盖（单席位无法单独达标），但提案应显式声明"独裁帽由权重 quorum 取代"并同步 UC，避免双重校验或双重缺失。
- **P2-4**　BLOCKING 的"管理员显式豁免"（§3.1）路径未定义：走 E7 override 还是新审计事件？建议绑定 E7 选项 `APPROVED` + note，并在 §6 人工接管条件中登记。
- **P3-1**　E4c 命名与 E4a/E4b（MERGING 内部转移）共享前缀但源状态不同（CONSENSUS_CHECK→REWORK），审计 grep 易混；建议改 E5b 或 E3a。
- **P3-2**　§6.1 配置示例中 `decision_threshold: 2/3` 与 `weight_quorum_ratio/seat_quorum_ratio` 语义重叠，建议合并或注释各自用途。

## 建议的闭环顺序与验收标准

1. **P0-1**：管理员显式裁定 F-13/F-16 推翻与否 → 提案 §10 增项、§11 增 PRODUCT-FACTS/UC 迁移行；
2. **P1-1/P1-2**：补 ABSTAIN 裁决与 E3/git 提交语义迁移清单；
3. P2/P3 随修订批处理；
4. 验收：修订版提案中 `grep -n "issues_summary\|汇总段"` 与最终裁定方向一致；§8 清单与 §4.4/§9 迁移步骤逐条可对账；§9.3 场景表增补"显式弃权（若保留）/BLOCKING 豁免"两个用例。

## Reviewer 自审记录

- 本轮按 §9 五项自检执行；P0-1 的判定依据（F-13 原文、UC 修复 commit `2cd45ed`、提案 §3.4/P-3 原文）均给出可复现引用；
- 声明：本 reviewer 是 UC-1/5/6 F-13 对齐修复（`2cd45ed`）的执行者，对"汇总段方案"存在路径依赖；P0-1 仅主张"推翻须显式裁定"，不预设立场——独立 disposition 方案在单一写者与不可变性上确有工程优势。
