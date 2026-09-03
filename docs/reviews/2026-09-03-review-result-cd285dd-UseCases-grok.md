# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`cd285dd`）

- **评审日期**：2026-09-03
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`cd285dd`（`fix(spec&schema): resolve a0123e8 review findings across dictator cap, vote_result_ref, E7 state and AEP budget`）
- **工作区 HEAD**：`6746294`（差量 = 三份 `cd285dd` 申请 + `STATUS.md`；用例/PRD/Schema 正文与 `cd285dd` 一致）
- **前序对象**：`a0123e8`（本人该轨 `YES_APPROVE`，P2×5；设计同步轨 `NO_APPROVE` P1×1）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`YES_APPROVE`
- **证据**：`BLOCKING` × 0；`ADVISORY` × 若干（P2/P3）；**无 P0、无 P1**

**结论：授予用例文档体系 L1 DOC-ALIGNED / PG-0。** 相对 `a0123e8`，本轨无 P1 回退。申请点名的 UC-6 `vote_result_ref` 已写入规范信封并过 `review_disposition` 契约。申请 §3 机验本机复跑成立。93/93 **不是** L2。

设计同步轨同日另文 [`2026-09-03-review-result-cd285dd-DesignSync-grok.md`](2026-09-03-review-result-cd285dd-DesignSync-grok.md)：**不授予**。原因是仓库根 `macao.yaml` 通不过本轮新增的 D-6 语义校验，不在本轨 13 份用例正文内。按 F-17，本票不是「有条件通过」。

---

## 0. Reviewer 自审

- 不采信申请「三方一致授予 / 100% 自洽」与 STATUS 自述；对 `a0123e8` 本轨 P2 与 UC-6 示例按现行原文 + 抽出 YAML 复验。
- 未把上轮本人 YES 当作本轮证据。
- 仪器：Draft-07（含 `$ref` store）；`validate_config` 语义层；控制字符；Schema 双副本；`unittest discover`；`compileall`。
- CODE 待实施项（加权引擎主体、E5a、`override resolve`）**NOT_APPLICABLE**（L1）。
- **漏审登记**：无连续同类漏审。本轮专门核 UC-6 是否真写了 `vote_result_ref`，以及抽出块能否过已收紧的 `required`。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | UC-6 示例与 PRD §2.5 / Schema `required` 同含 `vote_result_ref` |
| 2 | 「已完成 / 100%」 | 申请 §3 机验 **VERIFIED**；「残余细项完全闭环」对 P2-4 **VERIFIED**，对其余上轮 P2 **未全闭** |
| 3 | 确定性用语 | 各 UC 多为「待实现」✓；申请「100%」未标目标 |
| 4 | YAML/JSON 过 Schema | UC-6 / UC-3 / UC-1-gemini **PASS**（gemini 且过 `validate_config`） |
| 5 | P1 均附路径 | 本轨无 P1；P2 均附路径 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例控制字符 0 | `docs/usercases/*.md` 控制字节 **0** | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 抽出 YAML | 三份 **PASS**；UC-6 含 `vote_result_ref` | **VERIFIED** |
| valid 10/10、invalid 20/20 | 正例 10/10 Draft-07 PASS；反例 20/20 在项目校验器下 REJECTED | **VERIFIED**（3 份 macao_config 反例 Draft-07 单独 ACCEPTED，由 `validate_config` 语义层拒绝，见设计同步轨 P2） |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 93/93；compileall 0 | Ran 93 OK，33.6s；compile rc=0 | **VERIFIED** |

全库 `docs/**/*.md` 控制字节 0；份数 glob **208** / `git ls-files '*.md'` **196**（申请写 206，P3）。

---

## 二、上轮 grok（`a0123e8`）本轨项

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| L1 授予（无 P1） | **未回退** | UC-7 P1–P4 仍为 `CONSENSUS_CHECK`；UC-8 双轨仍在；处置路径仍为 `.macao/.dispositions/r<round>/` |
| **P2-4** UC-6 示例无 `vote_result_ref` | **VERIFIED 闭环** | `UC6-issue-triage-rework.md:44-47` 已写 `path/evidence_commit/sha256`；抽出块 `validate_review_disposition` **PASS** |
| P2-1 / P2-2 / P2-3 / P2-5 | **仍开放** | 见 §四 |

---

## 三、已对齐 / 已确认项

1. UC-6 规范信封与 PRD §2.5、`review_disposition.schema.json` 的 `vote_result_ref` 必填集同构。
2. UC-7 与 PRD §3.3 E7 同句：源态 `HOLD (CONSENSUS_CHECK)`，`APPROVED` 两步流。
3. UC-8 关卡 1 远端 `ls-remote` / 纯本地 `remote_name: null` 与 PRD §14.5 同句。
4. UC-1-gemini 配置过 Schema 且过 `validate_config`（N=3，quorum=2）。
5. 10/10、双副本、93/93 本机为真。

---

## 四、P2 / P3（不阻断本轨 PG-0）

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | UC-8 §6 验收标准第 2 条（L78）仍只写 `ls-remote` fail-closed，六条断言未覆盖纯本地分支（A3） |
| P2-2 | P2 | D-9 的 `reconcile` 在 `docs/usercases/` **零命中** |
| P2-3 | P2 | UC-5 L29 仍保留浮点「赞成加权占比」，与同节纯整数五重门禁并列 |
| P2-4 | P2 | 用例 README L9 仍写「通过自动化测试验证」；93/93 覆盖的仍是既有引擎主体 |
| P3-1 | P3 | 申请 Markdown 份数 206 与本机 glob/ls-files 对不上；「0 控制字符」结论为真 |

---

## 五、建议闭环顺序

1. 设计同步轨先修根 `macao.yaml` 的 quorum，避免 Loader 拒启本仓库。
2. 本轨 P2：UC-8 验收补纯本地；UC-5 删浮点句；README 标明 D-9 `reconcile` 缺口。
3. 闭合后再单列申请 **L2**：加权计票读取 `vote_weight`、disposition HOLD、纯本地 context 传递 `null`。

---

## 六、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| （无 P1） | — | — | — |

`vote`: `YES_APPROVE`
