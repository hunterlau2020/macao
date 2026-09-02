# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`a0123e8`）

- **评审日期**：2026-09-02
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`a0123e8`（`fix(spec&schema): resolve 4027cce expert review findings`）
- **工作区 HEAD**：`3b60d3a`（差量 = 三份 `a0123e8` 申请 + `STATUS.md`；用例/PRD/Schema 正文与 `a0123e8` 一致）
- **前序对象**：`4027cce`（本人 `NO_APPROVE`，P1×2：D-6 下界可关、`remote_name: null` 三真源）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`；提案 §2 D-1～D-9；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **定级申请**：L1 DOC-ALIGNED / PG-0
- **机器票**：`YES_APPROVE`
- **证据**：`BLOCKING` × 0；`ADVISORY` × 若干（P2/P3）；**无 P0、无 P1**

**结论：授予用例文档体系 L1 DOC-ALIGNED / PG-0。** 相对 `4027cce`，本人上轮两条阻断均已在用例正文、PRD §14.5 与契约写成同一条边：`remote_name: null` 可配置，关卡 1 远端 fail-closed / 纯本地本地校验并列；D-6 单键下界 `minimum_winning_seats ≥ 2`、`dictator_cap_enabled: const true` 已能拒绝上轮单席位反例。申请 §3 机验本机复跑成立。92/92 **不是** L2。

设计同步轨同日另文 [`2026-09-02-review-result-a0123e8-DesignSync-grok.md`](2026-09-02-review-result-a0123e8-DesignSync-grok.md)：**不授予**。提案 §4.5 与变更清单仍把 E7 源态写成 `CONSENSUS_CHECK 或 REWORK`，与 PRD §3.3 / 本轨 UC-7 冲突。实施须以 PRD 转移表与 UC-7 为准，不得按清单第 6 项给 `REWORK` 加 E7 边。该冲突不在本轨 13 份用例正文内，不阻断本票。按 F-17，本票不是「有条件通过」。

---

## 0. Reviewer 自审

- 不采信申请 §1/§4「全部阻断实质闭环 / 100%」与 STATUS 自述；对本人 `4027cce` P1-1 / P1-2 按现行原文 + 探针复验。
- 未把同日其他 reviewer 的票当作本轮证据。E7 源态残留在提案/清单，由本机 `grep` 与行号对照确认。
- 仪器：Draft-07（含 `$ref` store）；控制字符 `0x09/0x0b/0x0c/0x0d`；Schema 双副本；抽出 YAML；`unittest discover`；`compileall`；计票/配置探针。
- CODE（加权引擎、E5a、`override resolve`、纯本地派发）仍为清单待实施项，本轮 **NOT_APPLICABLE**（L1）。
- **漏审登记**：无连续同类漏审。本轮专门复跑上轮两条 P1 的反例，并核 UC-7 起态是否仍与 PRD 同句。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | UC-7 与 PRD E7 同句 `CONSENSUS_CHECK`；UC-8 与 §14.5 同句 `remote_name: null`。提案/清单 E7 **不同句**（他轨 P1） |
| 2 | 「已完成 / 100%」 | 申请 §3 机验 **VERIFIED**；「全部前序阻断闭环」对本轨 P1 **VERIFIED**，对全仓库施工图 **CONTRADICTED**（见设计同步轨） |
| 3 | 确定性用语 | 各 UC 多为「待实现」✓；申请「100%」未标目标 |
| 4 | YAML/JSON 过 Schema | UC-6 / UC-3 / UC-1-gemini **PASS**；`remote_name: null` **ACCEPTED** |
| 5 | P1 均附路径 | 本轨无 P1；P2 均附路径 |

---

## 一、申请 §3 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份用例控制字符 0 | `docs/usercases/*.md` 控制字节 **0** | **VERIFIED** |
| UC-6 / UC-3 / UC-1-gemini 抽出 YAML | 三份 **PASS**；gemini 示例已无 `min_effective_votes` | **VERIFIED** |
| valid 10/10、invalid 16/16 | 10/10 PASS；16/16 REJECTED | **VERIFIED**（其中 `aep_payload_oversized.json` 拒因是 `acceptance_criteria` 空数组，不是字节预算，登记他轨 P2） |
| Schema 双副本 0 diff | 8 份 SAME | **VERIFIED** |
| 92/92；compileall 0 | Ran 92 OK，42.2s；compile rc=0 | **VERIFIED** |

全库 `docs/**/*.md` 控制字节 0；份数 glob **201** / `git ls-files '*.md'` **187**（申请写 188，P3）。

---

## 二、上轮 grok（`4027cce`）阻断闭环

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** D-6：`minimum_winning_seats` 下界 1、`dictator_cap_enabled` 可 false | **VERIFIED 闭环**（单键约束） | `macao_config.schema.json:72-73`：`const: true`、`minimum: 2`。探针 `minwin=1` → `1 is less than the minimum of 2`；`dictator=false` → `True was expected`。反例 fixture 拒因与名义一致。`min_effective_votes` 已从用例与 `policy.required` 消失 |
| **P1-2** UC-8 `remote_name: null` 过不了契约，且 PRD §14.5 无本地豁免 | **VERIFIED 闭环** | 契约 `type: ["string","null"]`；正例 `macao_config_local_only.yaml` PASS；探针 `null` **ACCEPTED**。PRD L1505–1507 与 UC-8 L23–24 / A3 同为远端 `ls-remote` fail-closed / 纯本地跳过远端 |

上轮验收「`minimum: 2` + `const: true` + 反例 fixture」与「三选一并写进 Schema + §14.5 + UC-8」均已落到单键与关卡 1 正文。跨字段独裁帽公式（`3w_i < 2W`）仍归运行时，见设计同步轨 P2，不把上轮单键验收升格为「五重公式已物理锁死」。

`caf3473` / `5583bdd` / `6e35a71` 已闭项抽查：处置路径仍为 `.macao/.dispositions/r<round>/`；E7 `APPROVED` 仍为 override → `SHOULD_DISPOSE` → FINAL → E4；UC-7 触发仍为 P1–P4（均 `CONSENSUS_CHECK`）。**未回退。**

---

## 三、已对齐 / 已确认项

1. UC-8 关卡 1 与 PRD §14.5 同一条双轨边；`remote_name: null` 可被 `macao_config` / `review_context` 表达。
2. UC-7：P1–P4 进入态均为 `CONSENSUS_CHECK`；`APPROVED` 转移列与语义列均为两步流；禁代写、禁无 FINAL 直跳。
3. UC-6 守卫：精确穷尽、`FINAL` 禁 `NEEDS_ADMIN`、`requires_new_checkpoint` 分流 E4/E5a；抽出 YAML 过 `review_disposition`。
4. UC-1 两份示例不再写 `min_effective_votes`；gemini 配置过契约。
5. UC-5 五重纯整数公式与 D-6 同序；决策表三值。
6. 10/10、16/16、双副本、92/92 本机为真。

---

## 四、P2 / P3（不阻断本轨 PG-0）

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | UC-8 §6 验收标准第 2 条（L78）仍只写「未推送或 `ls-remote` 失败 → fail-closed」，六条断言均未覆盖本轮新增的纯本地分支（A3 / 关卡 1 第二段） |
| P2-2 | P2 | D-9 的 `reconcile` 在 `docs/usercases/` **零命中**；目录 README 守护行只列 UC-9/UC-10 |
| P2-3 | P2 | UC-5 L29 仍保留浮点「赞成加权占比 = Σ(approve 权重) / 有效权重」，与同节 L30–35 纯整数五重门禁并列 |
| P2-4 | P2 | UC-6 规范信封示例（L26–55）无 `vote_result_ref`，PRD §2.5 示例有；两端均过当前 Schema（该字段未进 `required`）。权威守卫列表未将其列为 fail-closed，故不升 P1 |
| P2-5 | P2 | 用例 README L9 写「通过自动化测试验证」；本轮 92/92 覆盖的仍是既有引擎主体，v2.5 计票 / E5a / `override resolve` 在清单中仍为待编码 |
| P3-1 | P3 | 申请 Markdown 份数 188 与本机 glob/ls-files 对不上；「0 控制字符」结论为真 |

---

## 五、建议闭环顺序

1. 设计同步轨先改提案 §4.5 L226 与清单 L85（删「或 `REWORK`」），避免施工图覆盖本轨已对齐的 UC-7。
2. 本轨 P2：UC-8 验收补纯本地断言；UC-5 删浮点句；UC-6 示例与 PRD §2.5 对齐 `vote_result_ref`；D-9 补 `reconcile` 分册或在 README 标明缺口。
3. 闭合后再申请 **L2**：加权计票读取 `vote_weight`、disposition HOLD、纯本地 `ReviewContextBuilder` 传递 `null`。

---

## 六、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| （无 P1） | — | — | — |

`vote`: `YES_APPROVE`
