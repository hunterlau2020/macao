# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`73576c5`）

- **评审日期**：2026-09-03
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`73576c5`
- **工作区 HEAD**：`34a1077`（差量 = 三份 `73576c5` 申请 + `STATUS.md`；用例/PRD/Schema 正文与 `73576c5` 一致）
- **前序对象**：`cd285dd`（本人该轨 `YES_APPROVE`，P2×4；设计同步轨 `NO_APPROVE` P1×1）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 1（P1）；`ADVISORY` × 若干（P2/P3）；**无 P0**

**结论：不授予用例文档体系 L1 DOC-ALIGNED / PG-0。** 相对 `cd285dd`，本轨无 P1 回退到「字段缺失」一类；UC-7 源态、UC-8 双轨、UC-6 `vote_result_ref` 三元组仍在。申请「用例正文 100% 稳定」不能代替「示例仍过现行契约」。本轮设计同步轨把 `review_disposition.schema.json` 收成 `additionalProperties: false` 之后，UC-6 规范信封仍含契约未声明的 `generated_at`。申请 §3 写「UC6 → review_disposition：**PASS**」本机为 **FAIL**。L1 要求 YAML 示例与 Schema 一致。按 F-17，不能用「正文没改所以沿用上轮 YES」代替本轮抽出校验。

设计同步轨同日另文 [`2026-09-03-review-result-73576c5-DesignSync-grok.md`](2026-09-03-review-result-73576c5-DesignSync-grok.md)：**不授予**。原因是提案 §4.3 同一字段。97/97 **不是** L2。

---

## 0. Reviewer 自审

- 不采信申请「连续两轮全票通过 / 用例 100% 稳定 / UC-6 PASS」。上轮本人 YES 不是本轮证据。
- 在 Schema 本轮收紧之后重新抽出 UC-6/UC-3/UC-1-gemini，而不是只确认「用例文件相对 `cd285dd` 无 diff」。
- CODE 待实施项（编排器权重接线、E7 直跳）**NOT_APPLICABLE** 于本轨 L1 文档结论；在申请把「运行时五道门禁打通」写成授予理由时，记为 P2，不升格为本轨 P1。
- **漏审登记**：无连续同类漏审。本轮强制项是「契约 `additionalProperties: false` 后，未改动的用例示例是否仍合法」。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | UC-6 有 `vote_result_ref` 三元组；**多写 `generated_at`，契约只有 `timestamp`**（P1-1） |
| 2 | 「已完成 / 100%」 | 申请 §3「UC-6 PASS」**CONTRADICTED** |
| 3 | 确定性用语 | 各 UC 多为「待实现」✓；申请「100%」未标目标 |
| 4 | YAML/JSON 过 Schema | UC-3 / UC-1-gemini **PASS**；UC-6 **FAIL** |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例控制字符 0 | `docs/usercases/*.md` 控制字节 **0** | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 抽出 YAML | UC-3 `dev_manifest` PASS；UC-1-gemini `validate_config` PASS（N=3，quorum=2）；**UC-6 `review_disposition` FAIL**（`generated_at`） | **CONTRADICTED**（申请写三份均 PASS） |
| valid 10/10、invalid 22/22 | 正例 10/10 Draft-07 PASS；反例 22/22 在项目校验器下 REJECTED | **VERIFIED**（3 份 macao_config 反例 Draft-07 单独 ACCEPTED，见设计同步轨 P2） |
| Schema 双副本 0 diff | 8 份 SAME；fixtures 0 diff | **VERIFIED** |
| 97/97；compileall 0 | Ran 97 OK；compile rc=0 | **VERIFIED**（不覆盖 UC 围栏抽出） |

全库 `docs/**/*.md` 控制字节 0；份数 glob **206** / `git ls-files '*.md'` **205**（申请写 212，P3）。

---

## 二、上轮 grok（`cd285dd`）本轨项

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| L1 授予（无 P1） | **回退** | 本轮新 P1-1：契约收紧后 UC-6 示例不再合法。UC-7 P1–P4 仍为 `CONSENSUS_CHECK`；UC-8 双轨仍在；处置路径仍为 `.macao/.dispositions/r<round>/` |
| **P2-4**（上轮已闭）UC-6 无 `vote_result_ref` | **未回退** | L44–47 仍有三元组；失败原因不是缺 ref |
| P2-1 / P2-2 / P2-3 / 原 P2-4 README | **仍开放** | 见 §四 |

---

## 三、已对齐 / 已确认项（不抵消 P1）

1. UC-7 与 PRD §3.3 E7 同句：源态 `HOLD (CONSENSUS_CHECK)`，`APPROVED` 两步流，禁无 FINAL 直跳。
2. UC-8 关卡 1 远端 `ls-remote` / 纯本地 `remote_name: null` 与 PRD §14.5 同句。
3. UC-1-gemini 配置过 Schema 且过 `validate_config`。
4. UC-3 `.dev.yml` 示例过 `dev_manifest`。
5. 根 `macao.yaml` 四席 quorum=3 已与 D-6 公式对齐（不在本轨 13 份正文内，但申请点名的「UC-1 / UC-10 根配置」本机成立）。

---

## 四、P1：进入本轨 PG-0 前应修正

### P1-1　UC-6 规范信封含 `generated_at`，通不过现行 `review_disposition` 契约

申请 §3.2：「`UC6-issue-triage-rework.md` 处置示例 → `review_disposition.schema.json`：**PASS**」。

**证据**：

1. `docs/usercases/UC6-issue-triage-rework.md:36`：`generated_at: "2026-09-01T12:10:00Z"`。
2. `docs/schemas/review_disposition.schema.json` 的 `properties` 只有 `timestamp`（L20），没有 `generated_at`；根对象 L121 `"additionalProperties": false`（本轮设计同步轨声称已落地的封闭）。
3. 抽出第一块 YAML：`validate_review_disposition` → `(False, "Additional properties are not allowed ('generated_at' was unexpected)")`。去掉该键或改名为 `timestamp` 后 **PASS**（`vote_result_ref` 三元组合法）。
4. 权威对照：PRD §2.5 与正例 fixture 用 `timestamp`。UC-6 与提案 §4.3 仍用旧键名。
5. 「用例正文相对上轮无变更」成立，但不能推出示例仍合法：契约在 `73576c5` 收紧了。

L1 最低条件含「所有 YAML/JSON 示例是合法可解析格式」。GUIDELINES §9.4 要求声称 YAML 的代码块字段名与正式 Schema 一致。

**验收**：UC-6 信封与 Schema `properties` 同键（建议 `timestamp`，与 PRD §2.5 一致）；抽出 `validate_review_disposition(...) == (True, None)`。申请不得再把未抽出的围栏写成 PASS。

---

## 五、P2 / P3（P1 闭合前不讨论本轨授予）

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | UC-8 §6 验收标准第 2 条（L78）仍只写 `ls-remote` fail-closed，六条断言未覆盖纯本地分支（正文 A3 已有） |
| P2-2 | P2 | D-9 的 `reconcile` 在 `docs/usercases/` **零命中** |
| P2-3 | P2 | UC-5 L29 仍保留浮点「赞成加权占比」，与同节纯整数五重门禁并列 |
| P2-4 | P2 | 用例 README L9 仍写「通过自动化测试验证」；97/97 仍不抽出 UC 围栏（本轮 P1-1 即反例） |
| P2-5 | P2 | 申请把「运行时五道门禁 / E4 守卫打通」写成授予理由。`orchestrator.py:597-600` 决策用 `evaluate()` 不读 `vote_weight`；同组加权票引擎为 `DEADLOCK`、无权重为 `REWORK_REQUIRED`。属 L2 范围，本轨不升格 P1 |
| P3-1 | P3 | 申请 Markdown 份数 212 与本机 glob/ls-files 对不上；「0 控制字符」结论为真 |

---

## 六、建议闭环顺序

1. **P1-1**：UC-6 示例删 `generated_at` 或改为 `timestamp`；测试覆盖「抽出 UC-6 YAML」。
2. 本轨既有 P2：UC-8 验收补纯本地；UC-5 删浮点句；README 标明 D-9 `reconcile` 缺口。
3. 闭合 P1 后重新申请本轨 **L1 / PG-0**。L2 另列：计票读取 `vote_weight`、E7 无 FINAL 不得进 `MERGING`。

---

## 七、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | UC-6 处置示例含 `generated_at`，被 `review_disposition.schema.json` `additionalProperties: false` 拒绝；申请写 PASS |

`vote`: `NO_APPROVE`
