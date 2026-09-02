# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（Round 2，`6e35a71`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md`](2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md)
- **申请声称基线**：`6e35a71`（`docs: close all Grok 5583bdd review findings (P1-1 E7 override edge, P1-2 D-1~D-9 alignment, P2/P3 cleanup)`）
- **工作区 HEAD**：`12a05e2`（仅新增两份 2026-09-02 申请 + 改 STATUS；用例/PRD/Schema 正文与 `6e35a71` 一致）
- **前序对象**：`5583bdd`（本人 `NO_APPROVE`，P1×2）；`caf3473`（本人 `NO_APPROVE`，P1×3）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 D-1～D-9（申请自指定义源）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`YES_APPROVE`
- **证据**：`BLOCKING` × 0；`ADVISORY` × 若干（P2/P3）；**无 P0、无 P1**

**结论：授予用例文档体系 L1 DOC-ALIGNED / PG-0。** 相对 `5583bdd`，本人上轮两条阻断均已在正文写成同一条边、同一套编号，不是换标题。申请 §4 机验本机复跑成立。86/86 与 YAML 过 Schema **不**升格为 L2：加权引擎、E5a、`override resolve` 仍为清单待编码项。

申请「100% 机器语义级对齐 / 全部前序阻断物理闭环」中，**P1 层成立**；残留压缩表、投影表滞后、D-9 `reconcile` 缺分册，登记为 P2，不阻断 PG-0。按 F-17，本票不是「有条件通过」。

---

## 0. Reviewer 自审

- 不采信 STATUS「全量阻断闭环」与申请 §1/§6 的 100% 表述；对上轮 P1-1 / P1-2 逐项重读原文并复跑机验。
- 未把同日 qwen `YES_APPROVE` 当作本轮证据。
- 仪器：Draft-07 校验 fixture 与从用例围栏抽出的 YAML；字节扫描 `0x09/0x0b/0x0c/0x0d`；`docs/schemas` vs `src/macao/schemas` 逐字节；`PYTHONPATH=src python3 -m unittest discover tests`；`compileall`；探针 `consensus_rule: 2/3_majority`。
- CODE（加权引擎、E5a、`override.py`）仍为各分册待实现项，**NOT_APPLICABLE**（本轮 L1）。
- 上轮验收「投影 `SHOULD_DISPOSE` 后再 E4」本轮对照 UC-7 转移列 **与** 语义列、Layer 1c、场景 6a/6a-1，未把 A2 单句当成已满足。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | 处置路径 UC-1/UC-6/README/PRD §2.5/Layer 1c **同句**。UC-7 转移列与语义列对 E4 时点 **同句** |
| 2 | 「已完成 / 100%」 | 申请 §4 机验 **VERIFIED**；「P1-1/P1-2 闭环」**VERIFIED**；「100% 机器语义」降为正文主边对齐，P2 残留不改票 |
| 3 | 确定性用语 | 各 UC 多为「待实现」✓；申请「100%」未标注目标 |
| 4 | YAML/JSON 过 Schema | UC-3 / UC-6 / gemini 配置示例 **PASS** |
| 5 | P1 均附路径 | 本轮无 P1；P2 均附路径 |

---

## 一、申请 §4 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例控制字符 0 | `docs/usercases/*.md` 控制字节 **0** | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 抽出 YAML 过契约 | 三份 **PASS** | **VERIFIED** |
| valid fixture 8/8 | 8/8 PASS | **VERIFIED** |
| invalid 7/7 拦截 | 7/7 REJECTED（含 `admin_override_invalid_choice.json`、`disposition_final_with_needs_admin.yml`、`vote_result_cancelled_decision.json`） | **VERIFIED** |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 86/86；compileall 0 | Ran 86，OK，30.091s；compile rc=0 | **VERIFIED** |
| （探针）`2/3_majority` 须拒 | `macao_config.schema.json` FAIL：不在 `['weighted_2/3_v1']` | **VERIFIED** |

全库 `docs/**/*.md` + `docs/schemas/**/*.json` 扫描 198 文件控制字节 0；Markdown **181** 份（申请 Design-Sync 轨写 179，计数漂移见该轨 P2，本轨声明范围为用例 13 份，结论为真）。

---

## 二、上轮 grok（`5583bdd`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** E7 `APPROVED` 有 issue 时出口边不能唯一推出 | **VERIFIED 闭环** | 见下专节 |
| **P1-2** 申请 §3 D-7 仍为 FSM，提案 D-7 为 AEP | **VERIFIED 闭环** | 本轮申请 §3 九行与提案 L34–L42 **同 ID 同义** |

`caf3473` 三条（本轮复核，未回退）：

| 项 | 判定 |
|---|---|
| 处置路径双真源 | **仍闭环**。全 `docs/usercases` 无 `.macao/executor.disposition.yml` 活动路径；权威句为 `.macao/.dispositions/r<round>/executor.disposition.yml` |
| YAML 过 Schema | **仍闭环**。三份抽出 PASS |
| E7 FINAL 写者 | **本轮升为出口边闭环**（写者句在 `5583bdd` 已改；时点/投影在 `6e35a71` 对齐） |

Claude/Qwen 历史项（独立抽查，非采信）：Type A/B 字母、`items[]`、UC-8 关卡 1 `ls-remote` fail-closed，正文仍在。

### P1-1 专节（E7 唯一边）

上轮失败模式：UC-7 **转移列**立即 `MERGING`，语义列/A2 等 FINAL；h1/h2 无 override 后 `SHOULD_DISPOSE`；Layer 1c 对 DEADLOCK 不读 override/FINAL。

本轮对照：

1. **UC-7 §2.c L35**：转移列与语义列均为「落盘 `admin_override.json`（解 HOLD，投影 `SHOULD_DISPOSE`）→ 执行者 FINAL（`EXEMPTED_BY_ADMIN`+`override_id`）→ 校验后 E4 → `MERGING`」。明文禁止无 FINAL 直跳、禁止管理员代写。
2. **UC-6 A2 L75**：管理员只写 override；执行者写 FINAL；编排器校验后 E4。与 UC-7 同序。
3. **UC-1-glm h1 L125、h2 L146**：`CONSENSUS_CHECK`（已出具 `admin_override` APPROVED 且待 FINAL）→ `NOTIFY_EXECUTOR_DISPOSE` / `SHOULD_DISPOSE`。
4. **PRD Layer 1c L776–790**：`decision == DEADLOCK` 时读 `admin_override.json`（`choice == APPROVED`）再读 FINAL；无 FINAL 保持 `CONSENSUS_CHECK`；有 FINAL 按 `requires_new_checkpoint` 走 E5a/E4。
5. **PRD 场景三 L911–912**：6a 只写 override + `SHOULD_DISPOSE`；**6a-1** 执行者 FINAL 后 E4。
6. **提案 §4.2 第 2 条 L134**：超时 APPROVED 改为执行者写 FINAL；已删「管理员替代签署」。

**推演**（DEADLOCK + `--choice APPROVED --exempt-issue-ids`）：下一动作唯一为执行者 FINAL，然后 E4。跟转移列、语义列、A2、Layer 1c、6a-1 同边。GUIDELINES §6「1:1 僵局」出口 **现可唯一推出**。

残留：PRD §3.3 E7 伴随动作仍压缩写「APPROVED → E4」；§14.2 未加 override 后 `SHOULD_DISPOSE` 行。识别入口与用例主表已唯一，记 P2-1 / P2-2，**不**把压缩表重新升为 P1。

### P1-2 专节（D 编号）

| ID | 提案 L34–L42 | 本轮申请 §3 | 判定 |
|---|---|---|---|
| D-1 | `vote_result` 不可变、DEADLOCK 即时落盘 | 同义；落点 UC-5/7/9 | **VERIFIED** |
| D-2 | 独立 `review_disposition` | 同义；路径与三态 | **VERIFIED** |
| D-3 | 显式 ABSTAIN + `source` | 同义；计入 `accounted`、不进 $E_N$/$E_W$ | **VERIFIED** |
| D-4 | `DEFERRED` | 同义 | **VERIFIED** |
| D-5 | `requires_new_checkpoint` 显式布尔 | 同义；E4/E5a 分流 | **VERIFIED** |
| D-6 | 纯整数五重门禁 | 同义 | **主体 VERIFIED**（UC-5 仍留「赞成加权占比」旁注，P2-5） |
| D-7 | AEP/1.1、Type E、16 KiB | **改为 AEP**，不再占 FSM | **VERIFIED**（申请层）；16 KiB 仍未进信封 Schema（P2-6） |
| D-8 | Evidence Ref，不改 `checkpoint_ref` | 同义；UC-8 关卡 1 | **VERIFIED** |
| D-9 | init / doctor / **reconcile** / adopt | 职责边界 + 单写者（略扩，不改编号） | **PARTIALLY_VERIFIED**：doctor/init/adopt 有分册；`docs/usercases/` **仍无 `reconcile`**（P2-3） |

上轮「Layer 1a 触发 E3」句已从申请删除。B-6 验收（编号与提案一致）**本轮成立**。

---

## 三、D-1～D-9 用例正文（摘要）

| 提案裁定 | 判定 | 摘要 |
|---|---|---|
| D-1 | **VERIFIED** | UC-5 三态 + 即时落盘；UC-7 不回写 `vote_result` |
| D-2 | **VERIFIED** | UC-6 全文；`FINAL` 禁 `NEEDS_ADMIN`；路径收敛 |
| D-3 | **VERIFIED** | UC-4 A2；UC-9 `source: "timeout"` |
| D-4 | **VERIFIED** | 枚举无 `BACKLOG` |
| D-5 | **VERIFIED** | UC-6 规则句 |
| D-6 | **主体 VERIFIED** | UC-5 五条；UC-1 h0(3) 已改为纯整数五重（L105–108） |
| D-7 | **主体 VERIFIED** | Type A/B/E/H 分册正确；信封 Schema 仍兼 `AEP/1.0` 且无 16 KiB |
| D-8 | **VERIFIED** | UC-8 关卡 1 `ls-remote`；关卡 6 为 Post-merge 封存（不再「提升 evidence」） |
| D-9 | **PARTIALLY_VERIFIED** | 见上；`docs/usecases → usercases` 软链存在 |

上轮 P2 抽查（申请声称已清理）：README 产物表 L91–101 **无重复行**；UC-1-glm f4 **9 规则**；UC-3 git 字段 **`branch: feature/x`**；gemini TUI **Schema v2.5**。属实。

---

## 四、GUIDELINES §6 反例库

相对 `5583bdd`，原先不能唯一推出的「1:1 + `--choice APPROVED --exempt-issue-ids` 之后」现可唯一推出（见 §二 P1-1）。其余 10 项主路径仍可从 UC-3/4/5/7/8/9 推出：缺 `signal: EXPLICIT`、未拓扑前进、重复票、超时弃权计入 `accounted` 但不进 $E_N$/$E_W$、接管超时保持 HOLD、未推送 evidence 关卡 1 fail-closed、`FINAL`+`NEEDS_ADMIN` 契约拒收。

全弃权/空 `issues_index` 的 DEADLOCK + APPROVED：Layer 1c 仍等 FINAL；UC-7 禁止无 FINAL 直跳。实现应按「空清单 FINAL」而非 E4「无 issue」捷径跳过处置文件（P2-1 压缩表风险，识别入口已锁）。

---

## 五、已对齐 / 已确认项

1. 处置活动路径全库与 PRD §2.5 / Layer 1c 同句。
2. E7 `APPROVED`：override → `SHOULD_DISPOSE` → 执行者 FINAL → E4，写者与时点唯一。
3. 申请 §3 D-1～D-9 与提案 L34–L42 同 ID 同义。
4. Type A = `DEVELOPMENT_STARTED`，Type B = `REVIEW_REQUEST`，Type E = `DISPOSITION_REQUIRED`。
5. `.review.yml` 问题列表字段名 `items[]`。
6. UC-8 六道关卡：关卡 1 Pre-merge Evidence fail-closed；关卡 6 Post-merge 封存。
7. 待审 YAML 三份过 Schema；反例 7/7；双副本 0 diff；86/86；compileall 0。
8. F-20 写者边界与 D-1/D-2 同向。
9. `docs/usecases` 软链指向 `usercases`。

---

## 六、P0 / P1

无。

---

## 七、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | PRD §3.3 E7 伴随动作仍压缩「APPROVED → E4」。识别入口 Layer 1c 与 UC-7 已要求 FINAL；实现不得按压缩表在无 FINAL 时进 `MERGING`。 |
| P2-2 | P2 | PRD §14.2 / FAQ Q12 未加「override APPROVED 且待 FINAL」→ `SHOULD_DISPOSE`。UC-1 h1/h2 已有。DEADLOCK 行与 `requires_disposition` 行可能同时看似命中；以 Layer 1c + UC-1 新行为准。 |
| P2-3 | P2 | 提案 D-9 的 `reconcile` 在 `docs/usercases/` 零出现；doctor 文仅提示 `daemon --once`。 |
| P2-4 | P2 | README 总览 L79 仍写合并成功后「全部产物**提升至** evidence ref」。UC-8 关卡 6 已改为 Post-merge 封存。 |
| P2-5 | P2 | UC-5 §2.b 仍定义「赞成加权占比 = Σ/有效权重」，与纯整数五重门禁并列；决策表以五重为准。 |
| P2-6 | P2 | `aep_envelope.schema.json`：`payload` 任意 object；`protocol` 仍含 `AEP/1.0`；16 KiB 未进契约（50 KiB 探针会 ACCEPT）。正文预算仍在。 |
| P2-7 | P2 | 申请钉 `6e35a71`，申请文件在 `12a05e2`。交付物 diff 仅申请 + STATUS。 |
| P2-8 | P2 | UC-1-gemini 步骤仍做 agmsg 历史「发言模式」画像；TUI 示例 `macao task start` 与 UC-2 `task create` 不一致。 |
| P3-1 | P3 | Layer 1c 未编码「所有 BLOCKING 均 `EXEMPTED_BY_ADMIN`」；场景 6a-1 / UC-6 A2 有文字。提案 §4.2 第 3 条「直接推进 MERGING」仍略压缩，守卫写在同一句。 |

---

## 八、建议闭环顺序（不阻断本票）

1. 编码 `override resolve --choice APPROVED` 时以 **Layer 1c + UC-7 L35** 为准：无 FINAL 不得 `MERGING`。
2. 下一差量：§14.2 补 override 后投影行；E7 伴随动作改为「落盘 override → 等 FINAL → E4」；README L79 与 UC-8 关卡 6 对齐；补 `reconcile` 分册或在 UC-10 写职责一句。
3. Schema 后续把 16 KiB / 禁 `AEP/1.0` 收进契约（可与 L2 同期）。
4. 更新 STATUS 登记本报告。不要用 86/86 宣称 L2。

---

## 九、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P2-1` | minor | `ADVISORY` | E7 压缩表「APPROVED → E4」；识别入口已等 FINAL |
| `grok/P2-2` | minor | `ADVISORY` | §14.2/FAQ 缺 override 后 `SHOULD_DISPOSE` |
| `grok/P2-3` | minor | `ADVISORY` | 用例目录无 `reconcile` |
| `grok/P2-4` | minor | `ADVISORY` | README 总览仍写「提升 evidence」 |
| `grok/P2-5` | minor | `ADVISORY` | UC-5 残留加权占比旁注 |
| `grok/P2-6` | minor | `ADVISORY` | AEP 信封未编码 16 KiB / 仍接受 1.0 |
| `grok/P2-7` | minor | `ADVISORY` | HEAD `12a05e2` vs 钉钉 `6e35a71` |
| `grok/P2-8` | minor | `ADVISORY` | gemini 语义画像 + `task start` |

`vote`: `YES_APPROVE`
