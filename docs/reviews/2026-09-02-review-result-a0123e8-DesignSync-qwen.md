# PRD v2.5 设计同步轨复审（基线 `a0123e8`）评审结论

- **评审日期**：2026-09-02
- **评审人**：qwen（独立评审）
- **评审对象**：`2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md`，钉死 `a0123e8`（HEAD `3b60d3a` 仅增申请/STATUS）
- **结论**：**不授予 L1 DOC-ALIGNED / PG-0（轨 A）。** 本人 4027cce 轮 5 项 BLOCKING 中 **4 项实质闭环、1 项部分闭环**（B-4 的开关/席位锁属实，权重算术门禁仍未落地）；但独立复现 **3 项新/残留 P1**（权重与独裁帽无语义校验、`vote_result_ref` 非必填、提案 §4.5 与清单 E7 源态"或 REWORK"残留），与 claude/codex/grok 同基线发现交叉印证。
- **结构化 issue**：`BLOCKING` × 3（P1）、`ADVISORY` × 3

## 1. 前序轮（4027cce）本人阻断闭环核验

| 项 | 独立复验 | 判定 |
|---|---|---|
| B-1 PRD 示例 × Schema 五处失配 | 全 PRD 13 个 schema 形态代码块经权威契约**全部通过**（§5.2 块为 `payload.review_context` 片段，解包后通过）；固化测试 `test_prd_snippets_schema.py` 2/2 OK | ✅ CLOSED |
| B-2 字节预算未入契约 | `envelope.py` `MAX_MESSAGE_BYTES=16384`/`MAX_INLINE_FIELD_BYTES` + `validate_budget` 接入 `create()`/`parse()`；`aep_payload_oversized` 反例拦截；Draft-07 无法表达整包字节，运行时承载属正确分工。**残留见 A-1**（嵌套字段与封闭性） | ✅ 主体 |
| B-3 E7/E9 源态冲突 + 提案"直接 MERGING" | PRD §3.3 E7 源态收敛为 `HOLD(CONSENSUS_CHECK)`、APPROVED 两步路径（→SHOULD_DISPOSE→FINAL→E4/E5a）；提案 :135 "直接"表述已删；E7/E9 源态一致（RETRY 边可达）。**残留见 B-3'**（提案 §4.5/清单未同步） | ⚠️ 部分 |
| B-4 D-6 门禁契约可关 | `dictator_cap_enabled=false` → REJECT ✓；`minimum_winning_seats=1` → REJECT ✓（两把表面锁已焊死）。**权重算术本体未校验 → 见 B-1'** | ⚠️ 部分 |
| B-5 根 macao.yaml 被自家契约拒绝 | 根配置校验 **VALID**；`remote_name: null` 被契约接受；`macao_config_local_only.yaml` 正例合法；PRD §14.5 Gate 1 远端/纯本地双分支在位 | ✅ CLOSED |
| A-2 实现层 AEP/1.0 | `types.py:28` 增 `DISPOSITION_REQUIRED`；`envelope.py` `PROTOCOL="AEP/1.1"`；`test_msg_bus.py` 断言 1.1 | ✅ CLOSED |

## 2. BLOCKING（P1，全部本机复现）

### B-1'　D-6 权重算术与独裁帽无任何层级校验（申请"物理锁死"声明被证伪）

- **复现**：合法正例改三席权重 `100/1/1`（`3×100=300 ≥ 2×102=204`，违反 ∀i 3w_i<2W）+ 双 quorum=1 → `validate_config` **ACCEPTED**；`ConfigManager.load_config` 同样 **ACCEPTED**（只上调 seat quorum，无权重/帽校验）
- **冲突基准**：申请 §1.2 "D-6 反支配门禁 Schema 物理锁死"；UC-5/UC-10"违反独裁帽 → 配置期拒绝"；提案 D-6 构成性门禁。实际锁死的仅是布尔开关与席位下界两把表面锁
- **修正**：配置加载期按权重执行 `3w_i < 2W` 与双 quorum 语义校验（或 quorum 全部派生、禁止覆写），补 `100/1/1`、边界等式、低 quorum 三类拒绝测试（与 codex P1-1、claude A-P1-2 三方同判）

### B-2'　`vote_result_ref` 未列入 disposition 契约 `required`，不可变绑定不可执行

- **复现**：`review_disposition.schema.json` required 9 项**不含** `vote_result_ref`；disposition 去掉该字段仍 **ACCEPTED**（fixture 本身亦无此字段）
- **冲突基准**：PRD :676 §2.5 规范示例与 :569 含 `vote_result_ref`（path/evidence_commit/sha256）；提案 :186-193 反向引用冻结要求。UC-6 与提案示例同样缺该字段（跨文档矛盾，UC 轨另计）
- **修正**：`vote_result_ref` 入 required 且对象封闭（path/evidence_commit/sha256 必填）；同步 UC-6/提案示例；补"缺 ref/伪 ref"负例（与 codex P1-2 同判）

### B-3'　E7 源态"或 REWORK"残留——按清单施工将实现被禁止的边

- **证据**：提案 §4.5 E7 行源态仍写 `HOLD（CONSENSUS_CHECK 或 REWORK）`；`v2.5_CODE_CHANGE_INVENTORY.md:85` E7 守卫同为"从 HOLD（CONSENSUS_CHECK 或 REWORK）"——均与权威表 `MACAO_PRD_v2.md:881`（仅 `CONSENSUS_CHECK`）矛盾；PRD :889 明文禁止表外路径
- **修正**：两处删"或 REWORK"（REWORK 耗尽场景的 HOLD 点在 CONSENSUS_CHECK，PRD §3.4 已明确）（与 grok/claude 同判）

## 3. ADVISORY（P2/P3）

- **A-1（P2）**：AEP 契约未封闭——8 类 payload 均无 `additionalProperties: false`；Type E 未强制 `task_id/vote_result_ref/issues_index_sha256/deadline`；运行时预算仅遍历 payload 第一层（嵌套 3000 字节长正文可过 `parse`，codex 证据，本机未重构复现但代码路径属实）。申请"8 类封闭 Payload"表述应更正（与 claude P2-2/4、codex P1-3 同源，严重度从 claude P2 判）
- **A-2（P3）**：申请"120 份结论报告"与受审树实计不符（`ls *result*`=124；STATUS 口径 128 含 2.5 轮与方法论 4 份）——计数口径第三轮复发（本人 4027cce A-3 同项）
- **A-3（P3）**：§14.5 五步与 UC-8 六关卡编号映射注记（前轮 A-4 延续，语义一致）

## 4. 机验复核

92/92 OK、`compileall` 0、fixtures 10/10 正例 + **16/16 反例拦截**（本人经仓库验证器全量复跑）、`docs/schemas` ↔ `src/macao/schemas` JSON 逐字节一致（仅 `__init__/__pycache__/README` 差异）——**申请 §3 机验全部为真**；失实仅在 §1.2/§1.4 的"物理锁死/封闭"语义表述（§2）。

## 5. 定级意见

**不授予本轨 L1**：B-1'~B-3' 三项均使"权威基准 ↔ 机器契约 ↔ 实施清单"不能唯一推出同一行为。修复面窄（配置期权重校验 + 一个 required 字段 + 两处删字），预计单轮闭环。与面板关系：与 claude（P1×2）/codex（P1×3）/grok（P1×1）构成本轨四方一致不授予。

## Reviewer 自审记录

- B-4 上轮只测两把表面锁，未构造权重反例——本轮采纳 codex/claude 同基线发现并**自行复现**后并入（§9：漏审登记，盲点为"锁的覆盖范围未穷举"）
- 对 STATUS L42 已调和的"预算分工"结论：采纳其"运行时承载属正确分工"判断，但封闭性缺失仍按证据定 P2
- 未采信同行结论作为判定依据，三条 P1 均有一手探针或原文行号；未覆盖：win32、Phase 1 实现
