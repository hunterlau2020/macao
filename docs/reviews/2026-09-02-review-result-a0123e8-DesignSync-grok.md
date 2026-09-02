# PRD v2.5 Design-Sync 独立评审结论（`a0123e8`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md)
- **申请声称基线**：`a0123e8`（`fix(spec&schema): resolve 4027cce expert review findings`）
- **工作区 HEAD**：`3b60d3a`（差量 = 三份申请 + `STATUS.md`；PRD/Schema/提案/清单正文与 `a0123e8` 一致）
- **前序对象**：`4027cce`（本人 `NO_APPROVE`，P1×2）；`6e35a71`（本人该轨 `YES_APPROVE`）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 1（P1）；`ADVISORY` × 若干；**无 P0**

**结论：不授予 PRD v2.5 设计同步轨 L1 DOC-ALIGNED / PG-0。** 相对 `4027cce`，本人上轮两条 P1 已真正改掉：D-6 单键下界锁死；`remote_name: null` 进入契约且 §14.5 写成双轨。PRD 正式示例 14/14 过契约，根 `macao.yaml` PASS。申请「E7 源态精准固化 / 提案彻底清理」**不成立**：权威转移表已收敛为 `HOLD (CONSENSUS_CHECK)`，提案自己的 §4.5 与交付物变更清单仍保留 `或 REWORK`。PRD L889 禁止表外路径；按清单施工会实现一条被禁止的边。

用例轨同日另文 [`2026-09-02-review-result-a0123e8-UseCases-grok.md`](2026-09-02-review-result-a0123e8-UseCases-grok.md)：**授予** L1（UC-7 与 PRD 同句）。本票只约束本轨交付物。92/92 **不是** L2。

---

## 0. Reviewer 自审

- 不采信申请 §1「全部 Schema 与 PRD 核心阻断项闭环」与「物理锁死 / 彻底清理」。
- 对本人 `4027cce` P1-1 / P1-2 按现行 Schema + 探针复验；对申请声称的 E7 清理按 PRD / 提案 / 清单位置对照，不采信标题。
- 仪器同用例轨。运行时只作佐证：`ConfigManager.load` 不拦 `100/1/1`；`AEPEnvelope.parse` 拦整信封 16 KiB、不拦嵌套 3000 字符。CODE 缺口不单独构成 L1 P1。
- **漏审登记**：`4027cce` 轮已登记「查枚举不查下界」。本轮下界已闭。本轮在申请写「提案彻底清理」之后仍把提案 §4.5 当正式转移表读完，避免只核对 §4.2 重写段。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | PRD 示例与契约本轮对齐；**E7 源态三处声明不一致**（P1-1） |
| 2 | 「已完成 / 100%」 | 申请 §3 机验 **VERIFIED**；「E7 彻底清理」「D-6 Schema 物理锁死五重公式」**CONTRADICTED** |
| 3 | 确定性用语 | 申请「100% / 物理锁死」未标目标 |
| 4 | YAML/JSON 过 Schema | PRD 六段 + 8 个 AEP **PASS**；上轮反例 `minwin=1` / `dictator=false` **REJECTED** |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| PRD 代码块 Draft-07 100% PASS | §2.1/2.2/2.3/2.5/5.2/§13 各 1 块 PASS；§2.4 八个 AEP 信封 PASS；根 `macao.yaml` PASS | **VERIFIED** |
| Markdown 0 控制字符 | 控制字节 **0**；份数 glob 201 / `git ls-files` 187，申请写 188 | 结论 **VERIFIED**；份数 **PARTIALLY**（P3） |
| valid 10/10、invalid 16/16 | 10/10、16/16 | **VERIFIED**（`aep_payload_oversized.json` 名义不符，P2） |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 92/92；compileall 0 | Ran 92 OK；compile rc=0 | **VERIFIED** |

`test_prd_snippets_schema.py` 运行出现未关闭文件句柄 `ResourceWarning`（P3）。

---

## 二、上轮 grok（`4027cce`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** D-6 单键下界可关；`min_effective_votes` 必填孤儿 | **VERIFIED 闭环** | `minimum_winning_seats.minimum: 2`；`dictator_cap_enabled.const: true`；`policy.required` 无 `min_effective_votes`。探针 `minwin=1` / `dictator=false` **REJECTED**。反例 fixture 拒因匹配名义 |
| **P1-2** `remote_name: null` 非法且 §14.5 无本地模式 | **VERIFIED 闭环** | 契约 `string \| null`；正例 fixture PASS；§14.5 L1505–1507 双轨与 UC-8 同句 |

上轮明确把 `3w_i < 2W` 与 `minimum_winning_seats ≤ N` 划为 Draft-07 表达不了的运行时项。本轮 **不**把该条升格为新的 Schema P1。Loader 仍不执行配置期独裁帽，见 P2-1。

`4027cce` 他方已闭项抽查（独立，非采信）：PRD 示例过契约；E4 关卡顺序起点仍为 Pre-merge；disposition 枚举联动 `DEFERRED+true` **REJECTED**；`dev_manifest` 核心引用必填；SRS L613 为 8 类 AEP/1.1。

---

## 三、已对齐 / 已确认项

1. D-1 / D-2 写者边界；DEADLOCK 即时落盘；override 不回写 `vote_result`。
2. PRD §3.3 E7 行（L881）源态为 `HOLD (CONSENSUS_CHECK)`；伴随动作为 override → `SHOULD_DISPOSE` → FINAL → E4/E5a。§4.2 L135「直接推进至 MERGING」已不存在。
3. §14.5 关卡 1 远端 / 纯本地双轨；契约承认 `null`。
4. D-6 两道**单键**反支配门禁可被 Draft-07 执行。
5. AEP 八类均有 per-type required payload；Type A `specification_summary` `maxLength: 2048` 对 3000 字符 **REJECTED**。运行时 `AEPEnvelope.parse` 拒绝 18 KiB+ 整信封。
6. 14/14 示例、10/10、16/16、双副本、92/92 本机为真。

---

## 四、P1：进入实施基线前应修正

### P1-1　E7 源态在权威转移表已收敛，提案 §4.5 与变更清单未跟

申请 §1.3 写：E7 源态「精准固化为 `HOLD (CONSENSUS_CHECK)`」，「提案彻底清理」。PRD 转移表已改对；**提案自己的状态转移修订表与 Phase 1 施工图没有改。**

**证据**：

| 位置 | E7 源态 | 本轮 |
|---|---|---|
| `docs/MACAO_PRD_v2.md:881`（§3.3 统一转移表，权威） | `HOLD`（`CONSENSUS_CHECK`） | 已收敛 |
| `docs/MACAO_PRD_v2.md:888-889` | HOLD 是 `CONSENSUS_CHECK` 的受控暂停；**除本表来源外不得引入其他路径** | 禁止表外边 |
| `docs/usercases/UC7-human-override.md:14-17` | P1–P4 进入态全部 `CONSENSUS_CHECK` | 与 PRD 同句 |
| `docs/PRD_CHANGE_PROPOSAL_v2.5.md:226`（§4.5 转移表修订） | `HOLD`（`CONSENSUS_CHECK` **或 `REWORK`**） | **未改** |
| `docs/v2.5_CODE_CHANGE_INVENTORY.md:85` 第 6 项 | 「从 HOLD（`CONSENSUS_CHECK` **或 `REWORK`**）接收管理员裁定」 | **未改** |

同文件提案 L214 仍写：`REWORK_REQUIRED` 处置超时「继续停在 `REWORK`」。这与 PRD「HOLD 只在 `CONSENSUS_CHECK`」以及 UC-7 P3（超时进入 `CONSENSUS_CHECK`）互斥。

从 `REWORK` 源态选 `RETRY_REVIEW` 仍无合法边：E9（L882）源态仅 `CONSENSUS_CHECK`。这正是 `4027cce` 要把 E7 源态收掉 `REWORK` 的原因。PRD 收了，施工图没收。

按清单 L85 实现 Orchestrator，会增加 PRD L889 明文禁止的路径；现有注释站在 PRD 一边（HOLD in `CONSENSUS_CHECK`）。施工图比权威更松，照图改会把已对齐的行为改错。

**验收**：提案 L226 与清单 L85 删去「或 `REWORK`」；提案 L214 与 PRD/UC-7 对齐超时停驻态。`grep -n 'CONSENSUS_CHECK` 或 `REWORK' docs/PRD_CHANGE_PROPOSAL_v2.5.md docs/v2.5_CODE_CHANGE_INVENTORY.md` 零命中。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | 配置期独裁帽仍非 Loader 语义：复制合法配置为权重 `100/1/1`、两 quorum=1，`validate_config()` **ACCEPTED**（`3*100 ≱ 2*102`）；`ConfigManager.load()` 成功，仅上调 `seat_quorum_required`→2，**不**校验权重 quorum 或 `3w_i < 2W`。申请「Schema 物理锁死 / 杜绝支配」过称。上轮已约定跨项归运行时，本条不升 P1，但不得再写成既成事实 |
| P2-2 | P2 | `vote_result_ref` 在 disposition Schema 为可选；正例 fixture 与提案 §4.3 示例均缺该字段，PRD §2.5 示例有。提案规则 6 写「必须反向引用」。删字段仍 `validate_review_disposition() == True`。PRD 守卫列表 1–4 未把它列为 fail-closed，故不升 P1 |
| P2-3 | P2 | 「8 类封闭 Payload」：8 个 `allOf` 分支已齐，但 payload 均无 `additionalProperties: false`；`protocol` 仍含 `AEP/1.0`。嵌套 `review_context.task_info.description` 3000 字符：Schema **ACCEPTED**，`AEPEnvelope.parse` **ACCEPTED**（只扫 payload 第一层字符串）。整信封 16 KiB 在契约层不拦、在 `parse()` 拦。`fixtures/invalid/aep_payload_oversized.json` 的 `specification_summary` 仅 44 字符，拒因是 `acceptance_criteria: []`；补 `minItems` 后 **ACCEPTED** |
| P2-4 | P2 | E4 伴随动作（L875）仍把「检出」与「ff_only 技术合并」分成关卡 2/3；§14.5 把合并写进第 2 步，CI/签字/push 编号整体错一位。清单 L94 Pre-merge 仍只写远端 `ls-remote`，未复述纯本地分支 |
| P2-5 | P2 | PRD §14.2 投影表仍无「override `APPROVED` 且待 FINAL」→ `SHOULD_DISPOSE` |
| P2-6 | P2 | `macao_config.policy` 无 `additionalProperties: false`：塞回已删的 `min_effective_votes` **ACCEPTED** |
| P3-1 | P3 | 申请文档份数不可复算；`test_prd_snippets_schema.py` 未关文件句柄 |

---

## 六、建议闭环顺序

1. **P1-1**（两行）：提案 §4.5 与清单 E7 守卫删「或 `REWORK`」，并改 L214 超时停驻态。
2. P2-2：`vote_result_ref` 进 disposition `required`，同步 UC-6 / 提案示例 / fixture。
3. P2-1 / P2-3 可与 L2 同期：Loader 拒 `100/1/1`；AEP 递归 2048 字节 + 负例 fixture 名实相符。
4. 闭合 P1 后重新申请本轨 **L1 / PG-0**。在施工图与 PRD 转移表同句之前，不得按清单给 `REWORK` 接 E7。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | E7 源态：PRD/UC-7 已收敛为 `HOLD(CONSENSUS_CHECK)`，提案 `:226` 与清单 `:85` 仍写 `或 REWORK`；PRD `:889` 禁止表外路径 |

`vote`: `NO_APPROVE`
