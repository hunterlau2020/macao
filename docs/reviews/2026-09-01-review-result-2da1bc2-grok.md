# PRD v2.5 Design-Sync 独立评审结论（`2da1bc2`）

- **评审日期**：2026-09-01
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`](2026-09-01-review-request-PRD-v2.5-Design-Sync.md)
- **对应 commit**：`2da1bc2`（`docs: close Claude and Codex review findings on 2766c69, harden schemas and fixtures`）
- **前序对象**：`0bc6247`（本人 `NO_APPROVE`，P0×1 + P1×4）；`2766c69`（本人未评；Claude/Codex `NO_APPROVE`，GLM/Qwen 授予）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22；提案 D-1～D-9
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 3（P1），`ADVISORY` × 若干；**无 P0**

**结论：不授予 L1 DOC-ALIGNED / PG-0。** 相对 `0bc6247`，FSM 三投影、DEADLOCK 即时落盘、§2.5 disposition 信封、AEP Type E、F-20/FAQ/UC-7 均已真实改写，不是换标题。申请 §5 的控制字符清零、8 份 Schema 双副本一致、fixture 正例/反例、86/86 测试，本机独立复跑均成立。

但申请 §4「对 `2766c69` 全部 9 项阻断 100% 物理闭环」不成立：配置契约仍接受已废止的 `2/3_majority`；待审 UC-6 示例无法通过自称唯一的 disposition Schema；E7 `APPROVED` 在有 issue 时仍推不出「谁写带 `EXEMPTED_BY_ADMIN` 的 FINAL」。这三处会使两个按文档实现的系统接受不同配置、拒收不同产物、或在人工放行后停在不同状态。按 F-17 / GUIDELINES §8，不能投有条件通过。

---

## 0. Reviewer 自审

- 上轮本人 P0-1（Layer 1b/1c / 场景三）按现行正文重读并对照伪代码，**VERIFIED 闭环**。
- 不采信申请「100% 闭环」；对 Codex P1-5 用 Schema 原文证伪。
- 仪器：Draft-07（`jsonschema`）校验 fixture 与探针；Python 按字节值 `0x09/0x0b/0x0c/0x0d` 扫文档；`PYTHONPATH=src python3 -m unittest discover tests`；`diff` 比较 `docs/schemas` 与 `src/macao/schemas`。
- 未把 `2766c69` 的 Claude/GLM 结论当作本轮证据。
- CODE 实现（加权引擎、E5a 守卫）仍为清单中的待实施项，**NOT_APPLICABLE**（L1 不要求 L2）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | PRD §2.5 与 Schema 同构（`disposition_status` / `dispositions[]` / `disposition_type`）；**UC-6 示例仍用 `executor_id`** |
| 2 | 「已完成 / 100%」是否有证据 | 申请 §5 四条机验 **VERIFIED**；申请 §4 Codex P1-5 **CONTRADICTED** |
| 3 | 确定性用语 | §3.1 仍标注「设计目标值」 |
| 4 | YAML/JSON 可解析 | 正例 8/8 PASS；PRD/提案围栏未再抽全量，抽查 §2.5 / vote_result / Type E 可解析 |
| 5 | P1 均附路径 | 是 |

---

## 一、上轮 grok（`0bc6247`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P0-1** 识别入口 / 场景三仍是 v2.3.1 | **VERIFIED** | Layer 1b：`accounted == configured`（PRD L751–756），无 `minimum_quorum` 提前返回。Layer 1c：`DEADLOCK` 保持 HOLD；`APPROVED`+`requires_disposition` 读 FINAL 后按布尔走 E5a/E4；`REWORK_REQUIRED`→E5；无 `RETRY_REVIEW`/`CANCELLED` 机器分支。场景三步骤 5 即时落盘 `decision: DEADLOCK`；6a–6e 只写 `admin_override.json`。 |
| **P1-1** disposition 三套字段且未进 PRD §2 | **PARTIALLY_VERIFIED** | PRD §2.5 与 `review_disposition.schema.json` 已统一为 `disposition_status` / `dispositions[]` / `disposition_type` / `rationale`。提案 §4.3 仍为 `status` / `items[]` / `decision` / `reason_ref`。UC-6 示例缺 `executor` 对象（见本轮 P1-2）。 |
| **P1-2** F-20 / Q12 / §6.1 / UC-7 / STATUS | **PARTIALLY_VERIFIED** | F-20 已写「D-1/D-2 落实」。FAQ Q12 含 `SHOULD_DISPOSE`；Q13 明确不回写 `vote_result`。§6.1 有 Disposition timeout 与 `NEEDS_ADMIN unresolved`。UC-7 验收改为 DEADLOCK 期间文件已存在且裁定不改哈希。**STATUS 仍把当前文档轨写成 `2766c69`、测试 84/84**（见 P2-1）。 |
| **P1-3** AEP 8 vs 7、缺 Type E | **VERIFIED**（示例层） | 8 类 Type A–H；Type E `DISPOSITION_REQUIRED` 完整 JSON 在 PRD L535+；fixture `aep_review_request.json` 为 `AEP/1.1` 且无 `content_base64`。字节预算仍未进入信封 Schema（P2-2）。 |
| **P1-4** 清单路径与仓库不符 | **VERIFIED** | 清单指向 `fsm.py` / `state_engine.py` / `merge/controller.py` / `cli/main.py`；`storage/evidence.py` 标「新建」。 |

---

## 二、申请声称已闭环的 `2766c69` 项（独立机验）

| 申请 §4 项 | 本轮判定 |
|---|---|
| Claude N-1 / Codex P1-1 公式控制字符 | **VERIFIED**。全 `docs/**/*.md` 与 `docs/schemas/**/*.json` 的 TAB/VT/FF/CR 计数为 **0**。PRD L332 为完好 `$\forall i, 3 \times w_i < 2 \times W$`。 |
| Claude N-2 / Codex P1-2 `vote_result.decision` | **VERIFIED**。枚举三值；`RETRY_REVIEW`+`human_override` 探针 **REJECT**；负例 `vote_result_cancelled_decision.json` **REJECTED**；`policy_snapshot` 等在 `required` 中。 |
| Codex P1-3 `review_context` 9 块 / 禁 base64 | **主体 VERIFIED**。`required` 10 键；Schema 树无 `content_base64`。**16 KiB 未进入 `aep_envelope.schema.json`**（payload 任意 object；50 KiB 探针 **ACCEPT**）。 |
| Codex P1-4 `FINAL`+`NEEDS_ADMIN` | **VERIFIED**。探针与负例 fixture 均 **REJECT**。`EXEMPTED_BY_ADMIN` 要求 `override_id`。 |
| **Codex P1-5 配置封闭 `weighted_2/3_v1`** | **CONTRADICTED**。见本轮 P1-1。 |
| Codex P1-6 README / `dev_manifest` | **VERIFIED**。README 写 PRD v2.5、三值 decision、10 块 context。 |
| Codex P1-7 UC-9 超时 ABSTAIN | **VERIFIED**。计入 `reviewers_accounted`，不计入 $E_N$/$E_W$（UC-9 L35–40）。 |

申请 §5：

| 声明 | 本机 |
|---|---|
| 控制字符 0 | **VERIFIED** |
| valid fixture 8/8 | **VERIFIED**（8 文件全部 PASS） |
| invalid 全部拦截 | **VERIFIED**（6/6 REJECTED） |
| `docs/schemas` vs `src/macao/schemas` 0 diff | **VERIFIED**（8 份 SAME） |
| 86/86 PASS；compileall 0 | **VERIFIED**（Ran 86，OK，53.3s；compile rc=0） |

---

## 三、已对齐 / 已确认项

1. D-1：机器 `decision` 三值；DEADLOCK 即时落盘；E7 写独立 `admin_override.json`。Layer 1c、场景三、UC-5、UC-7 主路径同向。
2. D-2 / D-5：PRD §2.5 信封 + 精确覆盖 + 必填布尔；E4/E5a 只认 `FINAL`。
3. D-6 公式可复制。独立复算 N=3、W=4、2 YES + 1 NO：席位 quorum 3≥2，权重 quorum 4≥3，`3×3≥2×4`，胜方席位 2≥2 → `APPROVED`。
4. Evidence Ref、§14.3–§14.5、第十五部分在正文中存在（抽查 E4 指向 §14.5、L1451/L1466 标题在位）。
5. `role_view` 含 `SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE`（PRD L1437 与 FAQ Q12）。
6. 现行测试集与 Schema 镜像在 **L1 仪器**意义上通过；它们 **不**证明 v2.5 计票/E5a 已实现（清单仍为待编码）。

---

## 四、P1：进入实施基线前应修正

### P1-1　配置契约仍接受已废止的 `2/3_majority`（申请 §4 Codex P1-5 未闭环）

申请写：「严格收敛 `policy.consensus_rule` 枚举为 `["weighted_2/3_v1"]`」。

**证据**：`docs/schemas/macao_config.schema.json:66`

```json
"consensus_rule": { "enum": ["weighted_2/3_v1", "2/3_majority"] }
```

`dictator_cap_enabled` 仅为可选 boolean，**没有**把 $3w_i<2W$ 建成 fail-closed。PRD §2.3 / §13 与清单以 `weighted_2/3_v1` 为唯一运行规则。

**影响**：按 Schema 加载的实现可以带着 v2.3.1 等权规则启动；按 PRD 实现的必须拒绝。这是计票公式的双真源，属于 GUIDELINES §8 点名的结构性变更。

**验收**：枚举仅 `weighted_2/3_v1`；补负例 fixture；配置期独裁帽为拒启条件（代码可留到 Phase 2，但契约不得再放行旧规则名）。

### P1-2　待审 UC-6 示例无法通过 disposition Schema

申请将 [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) 列为与 PRD §2.5 对齐的交付物。

**证据**：UC-6 L31 为 `executor_id: "cc-ds4"`，无 `executor` 对象。Draft-07 对 `review_disposition.schema.json` 报 `'executor' is a required property`。同目录正例 `docs/schemas/fixtures/valid/disposition.yml` 使用 `executor.id`，与 PRD §2.5 L649–653 一致。

另：UC-6 A2「管理员……将 BLOCKING issue 标记为 `EXEMPTED_BY_ADMIN`……放行至 `MERGING`」未说明是改 disposition 文件还是只写 override。若管理员写 disposition，违反 §16.1「执行者唯一写 `executor.disposition.yml`」。

**验收**：UC-6 YAML 与 §2.5 / Schema / fixture 逐字段同名且校验 PASS；A2 写明 Executor 在 override 之后提交含 `override_id` 的更高版本 FINAL，或写明 Orchestrator 只校验、不代写。

### P1-3　E7 `APPROVED` 有 issue 时，FINAL 写者与场景推演不能唯一推出

上轮 grok 处置超时后选 `APPROVED` 的出口问题，在 DEADLOCK/豁免主路径上仍在。

**证据**：

- §3.3 E4：有 issue 必须 FINAL 且全 `requires_new_checkpoint=false`。
- §3.3 E7：`APPROVED`（豁免未修复 BLOCKING）→E4。
- 场景三 6a（L885）：管理员 `--choice APPROVED --exempt-issue-ids …` 后「因……且**存在** FINAL disposition → `MERGING`」。步骤 5 只有 DEADLOCK 的 `vote_result`，**表中没有任何人写出该 FINAL**。
- UC-7 c：`APPROVED`「必须提供 FINAL disposition」。未写提供者。
- Layer 1c 在 `DEADLOCK` 时只返回 HOLD，**不读** `admin_override.json`。E7 若是命令型转移，识别入口与转移表如何接力，正文未给伪代码。

**推演**：DEADLOCK 且 `issues_index` 非空 → 管理员选 APPROVED 并豁免。

1. 若无 FINAL：E4 不得进 `MERGING`；6a 却写成已进。
2. 若 Orchestrator 代写 `EXEMPTED_BY_ADMIN`：破执行者垄断。
3. 若仍要 Executor 再写 FINAL：应投影 `SHOULD_DISPOSE`，而 DEADLOCK HOLD 行是 `AWAIT_HUMAN`；override 之后哪一行生效未定义。

超时路径 §6.1 Disposition timeout 的 `APPROVED` 选项面临同一缺口。

**验收**：在 §3.3/§3.4/UC-7 三处写死同一条边，例如：E7 `APPROVED` 且仍有未覆盖 issue → 记录 override、解除 DEADLOCK HOLD、投影 `SHOULD_DISPOSE`，Executor 提交含 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL 后再 E4；**禁止**无 FINAL 直跳 `MERGING`。用 GUIDELINES §6「1:1 僵局 + 管理员批准」逐步推演只能命中一行。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | `STATUS.md` 当前文档轨仍写 `2766c69`、测试 84/84、阻断仍是控制字符与旧 `decision` 枚举——与 `2da1bc2` 和申请 §5 不一致。 |
| P2-2 | P2 | PRD/清单称 AEP 16 KiB / 2048 为硬约束；`aep_envelope.schema.json` 的 `payload` 为任意 object，50 KiB 探针通过；`protocol` 仍含 `AEP/1.0`。README 把跨项规则推给运行时，与申请「Schema 硬约束」不完全同句。 |
| P2-3 | P2 | 场景二把「`APPROVED`+BLOCKING」与「`REWORK_REQUIRED`」写在同一步：前者应等 FINAL 再 E5a；Layer 1c 对后者立即 `REWORK`。实现者会选错等待点。 |
| P2-4 | P2 | 提案 §4.3 仍用 `status`/`items`/`reason_ref`，与权威 PRD §2.5 并存。 |
| P2-5 | P2 | `vote_result.resolution` 枚举 `automatic` 与 `AUTO_WEIGHTED_CONSENSUS` 同义；UC-5 A3 行标仍写 `resolution: human_override`。 |
| P2-6 | P2 | `EXECUTIVE_SUMMARY.md` 仍自称权威基准「现版本 v2.3」，产物表无 disposition。 |
| P3-1 | P3 | 工作区存在未跟踪的 `docs/usecases/`（与 `docs/usercases/` 平行）。不在 `2da1bc2` 内，但会造成检索双目录。 |
| P3-2 | P3 | Schema 不编码 $3w_i<2W$ 不等式（可留运行时），但须与 P1-1 的规则名收敛一起说明。 |

---

## 六、建议闭环顺序

1. P1-1：删掉 `2/3_majority` 枚举 + 负例。
2. P1-2：UC-6 示例改成与 §2.5 同一信封；澄清 A2 写者。
3. P1-3：E7 `APPROVED`+issue 的 FINAL 写者与 `role_view` 一行表。
4. 更新 STATUS 到 `2da1bc2` 本轮票型（含本报告）。
5. P2 可随 PRD 小差量或 Phase 1 Schema 收口。

闭合后可再评 **L1 / PG-0**。现行实现与 v2.3.1 行为在编码切换前保持不变。

**不建议**：以 86/86 或「fixtures 100% PASS」代替配置枚举与 UC 示例对账；不建议在 E7 出口未写死时开始写 `override.py`。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | `macao_config` 仍接受 `2/3_majority`；申请声称已删 |
| `grok/P1-2` | major | `BLOCKING` | UC-6 示例 `executor_id` 无法通过 disposition Schema；A2 写者含混 |
| `grok/P1-3` | major | `BLOCKING` | E7 `APPROVED` 有 issue 时 FINAL/`EXEMPTED_BY_ADMIN` 写者与场景 6a 不能唯一推出 |

`vote`: `NO_APPROVE`
