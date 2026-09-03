# PRD v2.5 Design-Sync 独立评审结论（`73576c5`）

- **评审日期**：2026-09-03
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md)
- **申请声称基线**：`73576c5`（`fix(consensus&workflow): resolve cd285dd review findings across pure integer math, vote schema, E4 disposition guard and macao.yaml quorum`）
- **工作区 HEAD**：`34a1077`（差量 = 三份申请 + `STATUS.md`；PRD/Schema/提案/清单/根配置正文与 `73576c5` 一致）
- **前序对象**：`cd285dd`（本人该轨 `NO_APPROVE`，P1×1：根 `macao.yaml` quorum 低于 $\lceil 2N/3\rceil$）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 1（P1）；`ADVISORY` × 若干；**无 P0**

**结论：不授予 PRD v2.5 设计同步轨 L1 DOC-ALIGNED / PG-0。** 相对 `cd285dd`，本人上轮 P1（根 `macao.yaml` 四席 quorum=2）已改掉：现为 `seat_quorum_required: 3` / `weight_quorum_required: 3`，`validate_config()` 与 `ConfigManager.load()` 均为 `(True, None)`；`test_root_macao_yaml_passes_semantic_validation` 本机通过。提案 §4.2「当前状态（HOLD）」零命中；E7 源态三处仍为 `HOLD（CONSENSUS_CHECK）`。PRD 正式示例过契约；97/97 为绿。

申请把 `review_disposition.schema.json` 全量 `additionalProperties: false` 列为本轮核心修复。该收紧本机成立，且 PRD §2.5 权威示例用的是契约允许的 `timestamp`。**同一份契约下，交付物 #3 提案 §4.3 处置信封示例仍写 `generated_at`，Draft-07 拒绝。** L1 要求「所有 YAML/JSON 示例是合法可解析格式」。97/97 只抽 PRD 围栏，不抽提案。按 F-17，不能投有条件通过。

用例轨同日另文 [`2026-09-03-review-result-73576c5-UseCases-grok.md`](2026-09-03-review-result-73576c5-UseCases-grok.md)：**不授予**（UC-6 示例同一字段）。本票只约束本轨交付物。97/97 **不是** L2：`ConsensusEngine.evaluate()` 在单测里走纯整数交叉乘法，但编排器决策路径仍用不带 `weight`/`policy` 的票面调用同一函数。

---

## 0. Reviewer 自审

- 不采信申请 §1「全部阻断物理闭环」与 §3「22/22 Schema 准确拦截」「97/97」。
- 对本人 `cd285dd` P1-1 按根文件 + `validate_config` / `ConfigManager.load()` 复跑；对申请新声称的 disposition 封闭、计票五门禁、E4 守卫用反例探针，不采信标题。
- 本轮专门在「契约刚加上 `additionalProperties: false`」之后抽出提案 YAML，而不是只跑 `test_prd_snippets_schema`（该测试不覆盖提案）。
- **漏审登记**：无。上一轮漏审模式是「只跑 Draft-07 放过活配置」；本轮对活配置与提案示例都跑了项目校验器。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | PRD §2.5 用 `timestamp`；提案 §4.3 / Schema 正例 fixture 用 `timestamp`；**提案示例写 `generated_at`，契约无此键**（P1-1） |
| 2 | 「已完成 / 100%」 | 申请 §3 机验套件主体 **VERIFIED**；「处置契约全封闭且示例对齐」**CONTRADICTED** |
| 3 | 确定性用语 | 申请「物理闭环 / 100%」未标目标 |
| 4 | YAML/JSON 过 Schema | PRD 示例 PASS；提案处置示例 **FAIL** |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| PRD 代码块 100% PASS、0 Warnings | `tests.test_prd_snippets_schema` 2/2 OK | **VERIFIED**（仅 PRD，不含提案） |
| 根配置语义与 Schema | `validate_config(macao.yaml)=(True, None)`；`ConfigManager.load` OK；`seat_quorum_required=3`、`weight_quorum_required=3`；`test_config` 10/10 | **VERIFIED** |
| `test_consensus` 5/5 | 5/5 OK；`[YES w=2, NO w=1, NO w=1]` → `DEADLOCK` | **VERIFIED**（引擎单测；编排器接线见 P2-5） |
| Markdown 0 控制字符 | 控制字节 **0**；glob `docs/**/*.md` **206** / `git ls-files '*.md'` **205**，申请写 212 | 结论 **VERIFIED**；份数 **PARTIALLY**（P3） |
| valid 10/10、invalid 22/22 | 正例 10/10 Draft-07+项目 PASS；反例项目校验器 22/22 REJECTED | **PARTIALLY_VERIFIED**（3 份权重/quorum 反例 Draft-07 ACCEPTED，见 P2-1） |
| Schema 双副本 0 diff | 8 份 schema SAME；fixtures 0 diff / 0 miss | **VERIFIED** |
| 97/97；compileall 0 | Ran 97 OK；compile rc=0 | **VERIFIED** |

---

## 二、上轮 grok（`cd285dd`）阻断与声称闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** 根 `macao.yaml` 四席 quorum=2 | **VERIFIED 闭环** | `macao.yaml:41-42` 均为 3；$N=4$ 时 $\lceil 8/3\rceil=3$。`validate_config` PASS；`ConfigManager.load` PASS |
| Claude A-P1-1 提案「当前状态（HOLD）」 | **VERIFIED 闭环** | `grep '当前状态（HOLD）' docs/PRD_CHANGE_PROPOSAL_v2.5.md` **0 命中**；L126–129 均为 `` `CONSENSUS_CHECK`（HOLD） `` |
| 申请声称 disposition 全封闭 | **契约闭环，提案示例未跟** | 根/`executor`/`full_document`/`items` 均为 `additionalProperties: false`；`disposition_unrecognized_property.yml` 拒因匹配。提案示例见本轮 P1-1 |
| 申请声称纯整数五门禁 | **引擎主体闭环，编排器决策路径未跟** | `engine.py:94-105` 为 $3w\ge 2E_W$。编排器 `collect_and_evaluate_consensus` 第一次 `evaluate()` 不传 `weight`/`policy`（P2-5） |

`4027cce`/`a0123e8` 已闭的单键 D-6 下界、`remote_name: null`、E7 源态 **未回退**。

---

## 三、已对齐 / 已确认项

1. 根 `macao.yaml`：$N=4$，两 quorum = 3，过 Schema 且过 `validate_config`。
2. E7 源态：PRD L881、提案 L230、清单 L85 均为 `HOLD（CONSENSUS_CHECK）`。
3. PRD §2.3 / §2.5 / §13 示例与 8 类 AEP 过 Draft-07。
4. `vote_result.schema.json`：`generated_at`/`task_id`/`executor_id` 必填；`resolution` 仅 `AUTO_WEIGHTED_CONSENSUS`/`HUMAN_OVERRIDE`；缺 `source` 拒绝。
5. `dictator_cap_enabled: false` / `minimum_winning_seats: 1` 仍被 Schema 拒绝；`[5,1,1]` 与过低 quorum 仍被 `validate_config` 拒绝。

---

## 四、P1：进入实施基线前应修正

### P1-1　提案 §4.3 处置信封示例通不过本轮刚封闭的 `review_disposition` 契约

申请 §1.3 把「根对象、`executor`、`full_document`、`dispositions.items` 全量 `additionalProperties: false`」列为核心修复。交付物 #3 是 `docs/PRD_CHANGE_PROPOSAL_v2.5.md`。

**证据**：

1. `docs/schemas/review_disposition.schema.json:20` 允许的时间字段名是 `timestamp`；`properties` **无** `generated_at`；L121 `"additionalProperties": false`。
2. 提案 L159 示例键为 `generated_at: "2026-09-01T12:10:00Z"`。抽出后 `validate_review_disposition` → `(False, "Additional properties are not allowed ('generated_at' was unexpected)")`。
3. 对照：PRD §2.5 L660 用 `timestamp`，`test_prd_snippets_schema` PASS；正例 fixture `docs/schemas/fixtures/valid/disposition.yml:2` 用 `timestamp`，10/10 之一。删掉提案示例的 `generated_at` 后同一对象 PASS；改名为 `timestamp` 亦 PASS。
4. 97/97 不解析提案围栏。只跑 PRD 抽检会漏。

这与 `4027cce`/`cd285dd`「收紧契约后权威示例/活文件未跟」是同一缺陷类。实现者若按提案 §4.3 照抄，产出物会被本轮宣称已落地的 fail-closed 契约拒绝。

**验收**：提案 §4.3 示例改为契约已有键（建议与 PRD §2.5 / 正例 fixture 一致用 `timestamp`），或把 `generated_at` 写进 Schema `properties`（若选定它为唯一时间字段，则 PRD/fixture 必须改名，禁止双名并存无说明）。抽出提案 YAML：`validate_review_disposition(...) == (True, None)`。`grep -n generated_at docs/PRD_CHANGE_PROPOSAL_v2.5.md` 在处置示例中为 0（或与 Schema `properties` 同名）。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | 申请「22/22 Schema 拦截」含 3 份仅语义层拒绝的配置反例（`dictator_weight_violation` / `low_seat_quorum` / `low_weight_quorum`）。Draft-07 单独均为 ACCEPTED。与 `schemas/README.md`「跨项归运行时」一致，但不得写成 Schema 物理锁死 |
| P2-2 | P2 | `aep_envelope.schema.json` 的 `protocol` 仍含 `AEP/1.0`；Type B + `AEP/1.0` 探针 ACCEPTED |
| P2-3 | P2 | `disposition_*_with_new_checkpoint` / `disposition_final_with_needs_admin` 缺 `vote_result_ref`，Draft-07 先因缺字段拒绝，拒因不是文件名所称的互锁维。`vote_result_cancelled_decision.json` 先因缺 `generated_at` 拒绝，尚未走到 `decision: CANCELLED` |
| P2-4 | P2 | 清单 L94 Pre-merge 仍只写远端 `ls-remote`，未复述 §14.5 纯本地分支；PRD E4 伴随动作 L875 仍只写 `ls-remote` |
| P2-5 | P2 | `orchestrator.py:572-600` 第一次 `ConsensusEngine.evaluate()` 的票面无 `weight`、不传 `policy`。同组 `[YES w=2, NO w=1, NO w=1]`：引擎加权 → `DEADLOCK`，无权重票面 → `REWORK_REQUIRED`。DEADLOCK 分支随后 `generate_vote_result` 亦不传 `reviewer_weights`。不改变本轨 L1 判定依据（L1 看文档），禁止把 97/97 写成 L2。`resolve_override` L912–913 仍把 `APPROVED` 映到 `MERGING`+`E7`；`state_engine.py` Layer 1c 仍 `APPROVED → E4` 不看 disposition |
| P2-6 | P2 | PRD §14.2 `role_view` 表仍无「override `APPROVED` 且待 FINAL」→ `SHOULD_DISPOSE` 行（UC-1 已有）。多轮登记 |
| P2-7 | P2 | 清单 §2.6 所列 `tests/unit/test_consensus_weighted.py` 等路径仓库中不存在；`tests/unit/` 为 0 |
| P3-1 | P3 | 申请文档份数 212 与本机 glob/ls-files 对不上 |

---

## 六、建议闭环顺序

1. **P1-1**：提案 §4.3（及任何处置示例）时间字段与 `review_disposition.schema.json` 对齐；加一条「抽出提案 YAML 必须 PASS」的测试，避免只抽 PRD。
2. P2-1/P2-3：反例 fixture 在名义维上自包含。
3. P2-5 单列申请 **L2**：编排器决策 `evaluate()` 传入 `weight`+`policy`；E7 `APPROVED` 不得无 FINAL 直跳 `MERGING`；Layer 1c 与 E4 守卫同句。
4. 闭合 P1 后重新申请本轨 **L1 / PG-0**。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | 提案 §4.3 处置示例含 `generated_at`，被本轮封闭的 `review_disposition` 契约拒绝；PRD §2.5 用的是 `timestamp` |

`vote`: `NO_APPROVE`
