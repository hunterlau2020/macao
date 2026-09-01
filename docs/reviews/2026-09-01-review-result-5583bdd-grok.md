# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`5583bdd`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-01-review-request-UseCases-v2.5-Alignment.md`](2026-09-01-review-request-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`5583bdd`（`docs: close all Claude, Grok, and Qwen caf3473 review findings across UseCases suite`）
- **工作区 HEAD**：`50e1c3f`（仅重提申请文件；用例正文与 `5583bdd` 一致）
- **前序对象**：`caf3473`（本人 `NO_APPROVE`，P1×3）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 D-1～D-9（申请自指定义源）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 2（P1），`ADVISORY` × 若干；**无 P0**

**结论：不授予 L1 DOC-ALIGNED / PG-0。** 相对 `caf3473`，上轮三条阻断里有两条已真正改掉：处置活动路径收敛到 `.macao/.dispositions/r<round>/executor.disposition.yml`；UC-3 / UC-6 / UC-1-gemini 抽出 YAML 均能过对应 Schema。Claude 的 Type 字母与 `items[]`、UC-8 关卡 1 Pre-merge `ls-remote` 也在用例正文里。申请 §4 机验本机复跑成立（含新增第 7 份反例）。

申请「前序全部阻断 **实质闭环** / 与提案 D-1～D-9 **严格对齐**」仍不成立。E7 `APPROVED` 有 issue 时，UC-7 转移列仍写立即进 `MERGING`，语义列和 UC-6 A2 却要等执行者 FINAL，且 `role_view` / Layer 1c 没有「override 之后」的一行；申请 §3 的 **D-7 仍是 FSM**，而自称权威源的提案 L40 **D-7 是 AEP/1.1**。这两处会让两套实现在人工放行后停在不同状态，或把协议裁定编到错误编号下。按 F-17 / GUIDELINES §8，不能投有条件通过。

---

## 0. Reviewer 自审

- 不采信 STATUS「全量阻断闭环」与申请 §1/§6 的 100% 表述；对上轮三条 P1 逐项机验或重读。
- 仪器：Draft-07 校验 fixture 与从用例围栏抽出的 YAML；字节扫描 `0x09/0x0b/0x0c/0x0d`；`docs/schemas` vs `src/macao/schemas` 逐字节；`PYTHONPATH=src python3 -m unittest discover tests`；`compileall`。
- CODE（加权引擎、E5a、`override.py`）仍为各分册待实现项，**NOT_APPLICABLE**（本轮 L1）。
- 上轮验收「投影 `SHOULD_DISPOSE` 后再 E4」本轮对照原文，未把 A2 单句当成已满足。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | 处置路径 UC-1/UC-6/README/PRD §2.5/Layer 1c **同句**。UC-7 转移列 vs 语义列对 E4 时点 **不一致** |
| 2 | 「已完成 / 100%」 | 申请 §4 机验 **VERIFIED**；「B-6 严格对齐 L34–42」「P1-2 闭环」**CONTRADICTED** |
| 3 | 确定性用语 | 各 UC 多为「待实现」✓；申请「100%」「全部实质闭环」未标注目标 |
| 4 | YAML/JSON 过 Schema | UC-3 / UC-6 / gemini 配置示例 **PASS**（上轮 P1-3 闭环） |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §4 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例控制字符 0 | 13/13 为 0 | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 抽出 YAML 过契约 | 三份 **PASS** | **VERIFIED** |
| valid fixture 8/8 | 8/8 PASS | **VERIFIED** |
| invalid 7/7 拦截 | 7/7 REJECTED（含 `admin_override_invalid_choice.json`） | **VERIFIED** |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 86/86；compileall 0 | Ran 86，OK，32.5s；compile rc=0 | **VERIFIED** |

---

## 二、上轮 grok（`caf3473`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** 处置路径双真源 | **VERIFIED 闭环** | UC-6 L24、README L97、UC-1 h0(2) L112、PRD L638、Layer 1c L780 均为 `.macao/.dispositions/r<round>/executor.disposition.yml`。全 `docs/usercases` 已无 `.macao/executor.disposition.yml` |
| **P1-2** E7 `APPROVED` 的 FINAL 写者不能唯一推出 | **未闭环**（写者句已改，出口边仍分叉） | 见本轮 P1-1。UC-6 A2 已写「执行者写 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL」。UC-7 转移列仍立即 E4；h2 无 override 后 `SHOULD_DISPOSE` |
| **P1-3** 用例 YAML 过不了 Schema | **VERIFIED 闭环** | UC-3 含 `evidence_commit: "e5f6a7b"`；gemini 示例 `consensus_rule: "weighted_2/3_v1"`；三份抽出校验 PASS |

Claude `caf3473` 项（独立抽查，非采信）：

| 项 | 判定 |
|---|---|
| U-2 AEP Type 字母 | **VERIFIED**。UC-2 L51 Type A；UC-4 L7 Type B；与 PRD §2.4 表一致 |
| U-3 `items[]` | **VERIFIED**。UC-4 e3 / §6.5 与 README 产物表为 `items[]` |
| U-4 UC-8 Pre-merge Evidence | **主体 VERIFIED**。关卡 1 为 `ls-remote` fail-closed。关卡 6 仍写「提升至 canonical evidence ref」（P2-1） |
| U-13 YAML | **VERIFIED**（同上 P1-3） |

Qwen B-6：申请声称已按提案 L34–42 重写 §3。**D-1～D-6 与提案同义**；**D-7 仍错**（本轮 P1-2）。

---

## 三、D-1～D-9（以提案 §2 为权威编号）

| 提案裁定 | 判定 | 摘要 |
|---|---|---|
| **D-1** `vote_result` 不可变、DEADLOCK 即时落盘 | **VERIFIED** | UC-5 / UC-7 |
| **D-2** 独立 `review_disposition` | **VERIFIED**（路径已收敛） | UC-6 全文；三态；`FINAL` 禁 `NEEDS_ADMIN` |
| **D-3** 显式 ABSTAIN + `source` 区分 | **VERIFIED** | UC-4 A2；UC-9 `source: "timeout"`，计入 `accounted`、不进 $E_N$/$E_W$ |
| **D-4** `DEFERRED` 取代 `BACKLOG` | **VERIFIED** | UC-6 / UC-1 枚举无 `BACKLOG` |
| **D-5** `requires_new_checkpoint` 显式布尔 | **VERIFIED** | UC-6 规则句 + E4/E5a 分流 |
| **D-6** 纯整数五重门禁 | **主体 VERIFIED** | UC-5 §2.b 五条。UC-1 h0(3) 仍留「加权占比 ≥ 2/3」（P2） |
| **D-7** AEP/1.1 + Type E + 16 KiB | **用例正文主体 VERIFIED；申请对照表 CONTRADICTED** | Type A/B/E/H 在分册正确。申请 §3 把 D-7 写成 FSM，AEP 塞进 D-8（P1-2） |
| **D-8** Evidence Ref，不改 `checkpoint_ref` | **主体 VERIFIED** | UC-8 关卡 1；UC-4 零 base64。关卡 6 仍「提升 evidence」（P2-1） |
| **D-9** init / doctor / reconcile / adopt | **PARTIALLY_VERIFIED** | doctor 只读在 UC-10。`reconcile` 在 `docs/usercases/` **零命中**。adopt 仅 UC-1 拼接残表 L61（P2-4） |

---

## 四、GUIDELINES §6 反例库

与上轮相同的 11 项主路径，10 项仍可从 UC-3/4/5/7/8/9 唯一推出（缺字段、未拓扑前进、重复票、超时弃权、接管超时保持 HOLD、未推送 evidence 现有关卡 1）。

**不能唯一推出**：1:1 僵局 + 管理员 `--choice APPROVED --exempt-issue-ids` 之后的下一动作（见 P1-1）。

---

## 五、已对齐 / 已确认项

1. 处置路径全库与 PRD §2.5 / Layer 1c 同句。
2. UC-6 示例 `executor` 对象、`EXEMPTED_BY_ADMIN` 契约守卫；A2 写者改为执行者（相对 `caf3473` 的「管理员标记并放行」）。
3. Type A = `DEVELOPMENT_STARTED`，Type B = `REVIEW_REQUEST`。
4. `.review.yml` 问题列表字段名 `items[]`。
5. UC-7 / README 五选项含 `EXTEND`。
6. UC-8 关卡 1 Pre-merge Evidence fail-closed。
7. 待审 YAML 三份过 Schema；反例 7/7；86/86。
8. F-20 写者边界与 D-1/D-2（提案编号）同向。

---

## 六、P1：进入实施基线前应修正

### P1-1　E7 `APPROVED` 有 issue 时，出口边仍不能唯一推出（上轮 P1-2 未闭）

写者句已改对，**时点与投影没有写成同一条边**。

**证据**：

1. UC-6 A2 L75：管理员只写 `admin_override.json`；**执行者**交含 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL；编排器校验后再 E4。这是唯一清楚的顺序。
2. UC-7 §2.c L35 **转移列**：`APPROVED` → **E4 → `MERGING`**（看起来裁定当下即进合并）。**语义列**：落盘 override 后，**执行者提交 FINAL 再**触发 E4。同一行两套时点。
3. UC-1 h1/h2 与 PRD §14.2：`CONSENSUS_CHECK`（HOLD: DEADLOCK）→ Executor `AWAIT_HUMAN` / `ASK_ADMIN`。**没有**「override 已落盘、等待 FINAL」→ `SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE` 的一行。override 之后下一通知仍指向管理员。
4. PRD Layer 1c L776–777：`decision == DEADLOCK` **只 HOLD**，不读 `admin_override.json`，也不读 disposition。按识别入口实现，执行者交了 FINAL 也不会离开 HOLD。
5. PRD 场景三 6a L897：override 当下「因……且**存在** FINAL → `MERGING`」。步骤 5 只有 DEADLOCK 的 `vote_result`，与 A2「override 之后执行者再写 FINAL」不同步。
6. 提案 §4.2 第 2 条仍允许处置超时「**管理员一并签署替代 FINAL**」，与 UC-6 执行者垄断及 §16.1 并列。

**推演**（DEADLOCK + `--choice APPROVED --exempt-issue-ids`）：

- 跟转移列 / PRD E7 字面：无 FINAL 也可进 `MERGING`。
- 跟 A2 / 语义列：必须等执行者 FINAL；但 `role_view` 仍是 `AWAIT_HUMAN`，谁 ping 执行者不唯一。
- 跟 Layer 1c：永远 HOLD。

**验收**：UC-6 A2、UC-7 §2.c **转移列与语义列**、UC-1 h1/h2、PRD Layer 1c / 场景 6a 写成同一条边：override 只落盘 → 解除「问管理员」HOLD → 投影 `SHOULD_DISPOSE` → Executor FINAL（`EXEMPTED_BY_ADMIN`+`override_id`）→ E4；**禁止**无 FINAL 直跳 `MERGING`；**禁止**管理员代写 disposition。Layer 1c 在 DEADLOCK 时必须能读合法 override+FINAL，或写明 E7 为命令型、识别入口不负责该边。删除提案「替代 FINAL」。

### P1-2　申请 §3 D-7 仍与自称权威源不一致（Qwen B-6 未闭）

申请 L44：「裁定编号与定义**严格对齐**」[`PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) §2 L34–L42。

**证据**：

| ID | 提案 L34–L42 | 申请 §3 |
|---|---|---|
| D-7 | **AEP/1.1**、第 8 类 `DISPOSITION_REQUIRED`、16 KiB | **FSM 三投影与 E1～E10**；且写成「**Layer 1a** 仅在全席位 accounted 时触发 E3」（识别入口里这是 **Layer 1b**，Layer 1a 是 `.dev.yml`） |
| D-8 | Evidence Ref，不改 source `checkpoint_ref` | Evidence Ref **再叠** AEP 零 base64 / 16 KiB（提案 D-7 的内容） |
| D-9 | init / doctor / **reconcile** / adopt | 单写者垄断（提案未把垄断权叫 D-9） |

提案没有「FSM」号。申请把 FSM 占成 D-7，把 AEP 挤进 D-8，等于重新发明一套编号，却声明与 L34–42 逐条一致。GUIDELINES §4：强声明必须可核验。B-6 的验收是编号与提案一致，不是「用例里碰巧也写了 AEP」。

**验收**：申请 §3 九行与提案九行 **同 ID 同义**；FSM 对齐写进 D-7 以外的段落（或 PRD §3.2），不要占用 AEP 的编号。D-7 行改为 Type A–H + 16 KiB 落点。删掉「Layer 1a 触发 E3」。

---

## 七、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | UC-8 关卡 6 仍写「本轮全部产物**提升至** `refs/macao/evidence/...`」。关卡 1 已要求该 ref **已推送**；PRD §14.5 第 5 步是 Post-merge Seal，不是再做一轮产物提升。页眉仍写「五道关卡」。 |
| P2-2 | P2 | README 产物表 L99–104 与 L99 前三行重复（`docs/reviews` / `state.db` / AEP 各两遍）。 |
| P2-3 | P2 | UC-1-glm 仍是拼接稿：L61–62 残表 + 第二个「## 2. 主成功场景」；f4 写 gitignore「8 规则」，代码与 UC-10 为 9。 |
| P2-4 | P2 | 提案 D-9 的 `reconcile` 在用例目录零出现；`adopt` 只出现在拼接残表。 |
| P2-5 | P2 | UC-1 h0(3)「赞成加权占比 ≥ 2/3」；UC-3 §8 仍问 `adoption.yml`。 |
| P2-6 | P2 | UC-1-gemini：YAML 已 v2.5，步骤 3 仍做 agmsg **语义画像**、步骤 4 仍写「默认 2/3 多数制」、TUI 仍印 `Schema v2.4`。 |
| P2-7 | P2 | 申请钉 `5583bdd`，申请文件在 `50e1c3f`。 |
| P2-8 | P2 | AEP 16 KiB 仍未进入 `aep_envelope.schema.json`（沿用 Design-Sync 轮）。 |
| P3-1 | P3 | UC-3 示例 `development.git.source_branch` vs Schema/fixture 的 `branch`。 |

---

## 八、建议闭环顺序

1. **P1-1**：UC-7 转移列改成与 A2 同一时点；h1/h2 与 PRD §14.2 加 override 后 `SHOULD_DISPOSE`；Layer 1c 或 E7 命令型伪代码写死 DEADLOCK+override+FINAL → E4；场景 6a 拆成「先 override、后 FINAL、再 E4」。
2. **P1-2**：申请 §3 D-7/D-8/D-9 按提案 L40–L42 逐字对齐。
3. P2-1～P2-3 同一差量：UC-8 关卡 6 只留 Post-merge Seal、README 去重、UC-1 去拼接、gitignore=9。
4. 更新 STATUS 登记本报告。不要用 86/86 或「YAML 3/3 PASS」代替 E7 边与 D 编号对账。

闭合后再评 **L1 / PG-0**。在 UC-7 转移列与 Layer 1c 写死之前，不要按「裁定当下 MERGING」实现 `override resolve --choice APPROVED`。

---

## 九、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | E7 `APPROVED`：UC-7 转移列立即 MERGING vs A2 等 FINAL；无 `SHOULD_DISPOSE`；Layer 1c 对 DEADLOCK 不消费 override/FINAL（上轮 P1-2 未闭） |
| `grok/P1-2` | major | `BLOCKING` | 申请 §3 D-7 仍为 FSM，提案 D-7 为 AEP/1.1；声称 B-6「严格对齐 L34–42」不成立 |

`vote`: `NO_APPROVE`
