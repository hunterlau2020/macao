# PRD v2.5 Design-Sync 独立评审结论（`cd285dd`）

- **评审日期**：2026-09-03
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md)
- **申请声称基线**：`cd285dd`
- **工作区 HEAD**：`6746294`（差量 = 三份申请 + `STATUS.md`；PRD/Schema/提案/清单/根配置正文与 `cd285dd` 一致）
- **前序对象**：`a0123e8`（本人该轨 `NO_APPROVE`，P1×1：E7 源态提案/清单未跟）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0（v2.5 实施基线）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 1（P1）；`ADVISORY` × 若干；**无 P0**

**结论：不授予 PRD v2.5 设计同步轨 L1 DOC-ALIGNED / PG-0。** 相对 `a0123e8`，本人上轮 P1（E7 源态）已改掉：提案 §4.5 L230 与清单 L85 均为 `HOLD (CONSENSUS_CHECK)`；`grep 'CONSENSUS_CHECK\` 或 \`REWORK'` 在非 reviews 文档 **0 命中**。`vote_result_ref` 已进 disposition `required`；`validate_config()` 能拒绝 `[5,1,1]` 与过低 quorum；AEP payload `additionalProperties: false` 与递归 2048 字节预算本机成立。PRD 正式示例 14/14 过契约。

申请「配置期硬门禁已物理闭环」仍不成立于**仓库自己的单一事实源**：根 `macao.yaml` 有 4 席 reviewer，却写 `seat_quorum_required: 2` / `weight_quorum_required: 2`，`validate_config()` 与 `ConfigManager.load()` 均拒绝（`ceil(2N/3)=3`）。PRD §13 把该文件定为配置单一事实源。93/93 未覆盖这条活配置。按 F-17，不能投有条件通过。

用例轨同日另文 [`2026-09-03-review-result-cd285dd-UseCases-grok.md`](2026-09-03-review-result-cd285dd-UseCases-grok.md)：**授予** L1。本票只约束本轨交付物。93/93 **不是** L2（`ConsensusEngine` 仍按人数浮点 2/3）。

---

## 0. Reviewer 自审

- 不采信申请 §1「全部阻断物理闭环」与「20/20 Schema 准确拦截」。
- 对本人 `a0123e8` P1-1 按提案/清单位置复读；对申请新声称的 D-6 / `vote_result_ref` / AEP 用反例探针，不采信标题。
- 仪器同用例轨。额外：Draft-07 **单独**跑反例，与 `validate_config` 对照，避免把语义层拒绝误报成 Schema 拒绝。
- **漏审登记**：无。本轮在声称「根配置已对齐」的背景下仍对 `macao.yaml` 跑了 `validate_config`，而不是只跑 Draft-07（根文件 Draft-07 为 PASS）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | E7 三处同句；**根配置 quorum 与 N=4 公式不同句**（P1-1） |
| 2 | 「已完成 / 100%」 | 申请 §3 机验套件 **VERIFIED**；「配置期硬门禁闭环」对活 `macao.yaml` **CONTRADICTED** |
| 3 | 确定性用语 | 申请「物理闭环 / 100%」未标目标 |
| 4 | YAML/JSON 过 Schema | PRD 示例 PASS；根文件 Schema PASS、**语义校验 FAIL** |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| PRD 代码块 100% PASS、0 Warnings | §2.1/2.2/2.3/2.5/5.2/§13 各 1 块 PASS；§2.4 八个 AEP PASS；`unittest` 汇总未见 ResourceWarning | **VERIFIED** |
| Markdown 0 控制字符 | 控制字节 **0**；份数 glob 208 / `git ls-files` 196，申请写 206 | 结论 **VERIFIED**；份数 **PARTIALLY**（P3） |
| valid 10/10、invalid 20/20 | 正例 10/10 Draft-07 PASS；反例在 `test_schema` 所用校验器下 20/20 REJECTED | **PARTIALLY_VERIFIED**（3 份权重/quorum 反例 Draft-07 ACCEPTED，见 P2-1） |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 93/93；compileall 0 | Ran 93 OK；compile rc=0 | **VERIFIED** |

`init` 模板 `DEFAULT_CONFIG_TEMPLATE` 过 `validate_config`（测试覆盖）。**仓库根 `macao.yaml` 不在该 93 条之内。**

---

## 二、上轮 grok（`a0123e8`）阻断与 P2 闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** E7 源态提案 §4.5 / 清单未跟 | **VERIFIED 闭环** | 提案 L230：`HOLD`（`CONSENSUS_CHECK`）。清单 L85 第 6 项同句。提案 L218 超时停驻为 `CONSENSUS_CHECK`。验收 grep 零命中 |
| **P2-1** Loader 不拦 `100/1/1` 与过低 quorum | **主体闭环，活配置未跟** | `validate_config` 拒绝 `[5,1,1]`（`3*5=15 >= 2*7=14`）及两份低 quorum fixture；`ConfigManager.load()` 同步拒绝。根 `macao.yaml` 见本轮 P1-1 |
| **P2-2** `vote_result_ref` 非必填 | **VERIFIED 闭环** | Schema `required` 含该键；缺字段探针 REJECTED；正例 fixture / PRD §2.5 / 提案示例 / UC-6 均有三元组 |
| **P2-3** AEP 未封闭、嵌套 2048 不拦、oversized 名不副实 | **主体闭环** | Type A 额外字段 REJECTED；嵌套 `description` 3000 字节 `parse` REJECTED；`aep_payload_oversized.json` 2942 字符，拒因 `is too long`。`protocol` 仍含 `AEP/1.0`（P2-2） |

`4027cce` 已闭的单键 D-6 下界与 `remote_name: null` **未回退**。

---

## 三、已对齐 / 已确认项

1. E7 源态：PRD L881、提案 L230、清单 L85、UC-7 同为 `HOLD (CONSENSUS_CHECK)`。
2. D-6 配置期公式已进 `validate_config()`：独裁帽、`2 ≤ mws ≤ N`、两 quorum 下界；对应三份反例 fixture 拒因匹配名义。
3. disposition `vote_result_ref` 必填；缺字段 fail-closed。
4. AEP 8 类 payload `additionalProperties: false`；Type E 六项必填；运行时递归预算成立。
5. PRD 示例 14/14 与 §13 配置示例（N=3，quorum 2/3）过契约且过 `validate_config`。

---

## 四、P1：进入实施基线前应修正

### P1-1　仓库根 `macao.yaml` 通不过本轮宣称已落地的 D-6 配置期校验

PRD §13 L1390：位置是仓库根 `macao.yaml`，且「正文出现的全部数值均为该文件的默认值」。本轮申请把 `validate_config()` / `ConfigManager.load()` 的纯整数语义校验列为核心修复。

**证据**：

1. 根文件 `macao.yaml:16-42`：4 名 reviewer，权重均为 1 → $N=4$，$W=4$；`seat_quorum_required: 2`，`weight_quorum_required: 2`。
2. 本轮公式：$E_N$/$E_W$ 配置值须 $\ge \lceil 2N/3 \rceil = \lceil 8/3 \rceil = 3$。PRD §13 示例自身写对了（三席、席位 2、权重 3）。
3. 探针：`validate_config(yaml.safe_load(open("macao.yaml")))` → `(False, 'seat_quorum_required (2) is less than required minimum ceil(2N/3) = 3')`。`ConfigManager.load()` 对同一文件同样失败。该文件 Draft-07 **ACCEPTED**，故只跑 Schema 会漏掉。
4. 93/93 用的是 `DEFAULT_CONFIG_TEMPLATE` 与独立 fixture，**不加载仓库根文件**。申请「配置期硬门禁 100% fail-closed」对活配置不成立。

按该文件启动本仓库会在配置期被拒绝；按 Draft-07 实现则会接受与 D-6 冲突的 quorum。两种下一动作。这与 `4027cce`/`a0123e8`「收紧契约后根配置/示例未跟」是同一缺陷类。

**验收**：根 `macao.yaml` 的两 quorum 改为 $\ge 3$（或减到 3 席并保持与 §13 示例一致）；增加「加载仓库根 `macao.yaml` 必须 `validate_config` PASS」测试；`PYTHONPATH=src python3 -c "from macao.core.schema import validate_config; import yaml; print(validate_config(yaml.safe_load(open('macao.yaml'))))"` 输出 `(True, None)`。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | 申请「20/20 Schema 拦截」含 3 份仅语义层拒绝的配置反例（`dictator_weight_violation` / `low_seat_quorum` / `low_weight_quorum`）。Draft-07 单独均为 ACCEPTED。与 `schemas/README.md`「跨项归运行时」一致，但不得写成 Schema 物理锁死 |
| P2-2 | P2 | `aep_envelope.schema.json` 的 `protocol` 仍含 `AEP/1.0`；Type C + `AEP/1.0` 探针 ACCEPTED |
| P2-3 | P2 | `disposition_*_with_new_checkpoint` / `disposition_final_with_needs_admin` 缺 `vote_result_ref`，Draft-07 先因缺字段拒绝。补上 ref 后互锁仍 REJECTED（名义约束仍在），但 fixture 当前拒因不是文件名所称的那一维 |
| P2-4 | P2 | 清单 L94 Pre-merge 仍只写远端 `ls-remote`，未复述 §14.5 纯本地分支；E4 伴随动作与 §14.5 关卡编号仍错一位 |
| P2-5 | P2 | `ConsensusEngine` 仍按人数浮点 2/3（`engine.py:57-67`），不读 `vote_weight`。不改变 L1 判定依据，禁止把 93/93 写成 L2 |
| P3-1 | P3 | 申请文档份数不可复算 |

---

## 六、建议闭环顺序

1. **P1-1**：根 `macao.yaml` 两 quorum 与 $N=4$ 对齐（或席位数与 §13 示例对齐）+ 根文件回归测试。
2. P2-1/P2-3：反例 fixture 在「名义维」上自包含（互锁 fixture 带 `vote_result_ref`；语义反例标明走 `validate_config` 而非纯 Draft-07）。
3. P2-2 / P2-5 可与 L2 同期：禁 `AEP/1.0` 或标明只读兼容；计票引擎改纯整数五重门禁。
4. 闭合 P1 后重新申请本轨 **L1 / PG-0**。在根配置能被 `ConfigManager.load()` 接受之前，不得把「配置期硬门禁」写成已实施基线。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | 根 `macao.yaml` 四席仍写 quorum=2，`validate_config`/`load` 拒绝（ceil(2N/3)=3）；PRD §13 将该文件定为单一事实源 |

`vote`: `NO_APPROVE`
