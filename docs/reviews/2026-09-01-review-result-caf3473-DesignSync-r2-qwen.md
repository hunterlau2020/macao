# PRD v2.5 Design-Sync 复审（第二轮，`2766c69` 轮 9 项阻断闭环复核）评审结论

- **评审日期**：2026-09-01
- **评审对象**：`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`（更新版，新增 §4 闭环表）；实际基线 **`caf3473`**（HEAD；§4 声明整改落于 `2da1bc2`/`caf3473`，与 STATUS.md 一致）
- **评审人**：`qwen`（独立评审，全部声明逐项机验；对本评审人第一轮 `2026-09-01-review-result-2766c69-glm.md` 的 APPROVE 范围与本轮差异如实区分）
- **机器票**：**`NO_APPROVE`**（理由见 §3，非因核心交付物未闭环，而是申请范围内 UC 交付物存在未修复阻断）
- **结构化 issue**：`BLOCKING` × 1（范围级，引用平行评审 6 项）、`ADVISORY` × 2

---

## 1. `2766c69` 轮 9 项阻断闭环核验（本轮新增声明，全部独立复核）

| # | 专家项号 | 声明 | 独立核验证据 | 判定 |
|---|---|---|---|---|
| 1 | Claude N-1 / Codex P1-1 | PRD 控制字符清零 | 本机重放全库扫描（`docs/**/*.md`）：**0 控制字符** | ✅ VERIFIED |
| 2 | Claude N-2 / Codex P1-2 | vote_result 三值收敛 + required 收紧 | 实测：`required` 含 `policy_snapshot`/`vote_breakdown`/`issues_index`/`issues_index_sha256`/`requires_disposition`；`decision` 严格三值、**无** `RETRY_REVIEW`/`CANCELLED`；`resolution` 仅 `automatic`/`AUTO_WEIGHTED_CONSENSUS`；旧 `vote_result_human_override` 已移出正例集（valid 目录 8 份不含），反例 `vote_result_cancelled_decision.json` 在列且实测被拒 | ✅ VERIFIED |
| 3 | Codex P1-3 | review_context/AEP 无 base64 | `content_base64` 不在 `review_context.schema.json`；`base64` 不在 `aep_envelope.schema.json` | ✅ VERIFIED |
| 4 | Codex P1-4 | disposition FINAL 禁 NEEDS_ADMIN + EXEMPTED_BY_ADMIN 约束 | Schema 实测含 `NEEDS_ADMIN` 守卫、`EXEMPTED_BY_ADMIN`、`override_id`；反例 `disposition_final_with_needs_admin.yml` 实测被拒 | ✅ VERIFIED |
| 5 | Codex P1-5 | consensus_rule 收敛 | `macao_config.schema.json` 仅 `weighted_2/3_v1`；`2/3_majority` 零命中 | ✅ VERIFIED |
| 6 | Codex P1-6 | schemas README + dev_manifest 升 v2.5 | `docs/schemas/README.md` 头部"对应 PRD v2.5 权威基准"，8 契约表含 disposition/admin_override 及 `.macao/.dispositions/r<round>/` 权威路径；`dev_manifest` 字段统一（`full_document` required 含 `evidence_commit`） | ✅ VERIFIED |
| 7 | Codex P1-7 | UC-9 超时弃权边界 | `UC9-timeout-daemon.md:31/36-41/51`：计入 `accounted`、严格排除于 $E_N$/$E_W$、`source:"timeout"`、迟到票 `LATE_REVIEW_ISOLATED` 隔离 | ✅ VERIFIED |
| 8 | Claude N-11 | MVP 标题修正 | `MACAO_PRD_v2.md:908` "严格的 MVP 范围（第一期）"；"第二期" 零命中 | ✅ VERIFIED |
| 9 | Claude N-12 | §13 配置含 model | `MACAO_PRD_v2.md:1367-1371` executor + 4 reviewer 均含 `model` | ✅ VERIFIED |

## 2. 回归核验（防止闭环修复引入退化）

| 项 | 结果 |
|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests` | **86/86 OK**（本机重跑） |
| fixtures：valid 8/8、invalid 6/6 拦截 | ✅ 全部重放通过（含 `disposition_final_with_needs_admin`、`vote_result_cancelled_decision`、`review_abstain_invalid`、`review_status_vote_conflict`） |
| `docs/schemas/` vs `src/macao/schemas/` | ✅ 0 diff |
| PRD §3.2 Layer 1b/1c、§3.4 场景三（第一轮核验项） | ✅ 无回退（`accounted == configured`、DEADLOCK 即时落盘 + 独立 `admin_override.json` 仍在） |

**小结**：申请 §4 声称的 9 项阻断 **9/9 物理闭环**，无"声明修复、实际残留"；核心交付物（交付物 1~7、13：PRD、Schema 库、提案、代码清单、SRS、FAQ、PRODUCT-FACTS、STATUS）达到 L1 DOC-ALIGNED 水准。

## 3. 阻断原因（范围级，单列）

### B-0　申请范围内的用例交付物（#8~#12）存在 6 项未修复 BLOCKING，本轮不能授予

- **证据**：本申请 §2 交付物表第 8~12 行明确包含 `UC1/UC5/UC6/UC7/UC8/UC9`；在同一基线 `caf3473` 上，本评审人平行评审（`docs/reviews/2026-09-01-review-result-caf3473-qwen.md`）判定 **NO_APPROVE，BLOCKING × 6**：B-1 处置路径分裂（`.macao/executor.disposition.yml` vs Layer 1c 读取路径）、B-2 AEP Type 字母错位、B-3 `issues[]` vs `items[]`、B-4 UC-8 缺 Pre-merge Evidence Push 关卡且封存顺序倒置、B-5 UC-3 示例缺 `evidence_commit` + UC-1-gemini 停留 v2.4、B-6 申请系文档 D-1~D-9 编号与权威裁定表错位。Claude/Grok 同基线报告与其中 5 项一致。
- **自洽性证据**：未提交的 `STATUS.md` 工作区版本自身已写明"用例体系**暂不得作为 Phase 1~5 的官方操作基准**"、"v2.5 全文档体系（含用例）仍未获 PG-0"。
- **结论**：在交付物 #8~#12 的 6 项 BLOCKING 修复前，对**本申请整体**投 `NO_APPROVE`；若委员会决定拆轨，则交付物 #1~#7、#13 可单独授予 **L1 DOC-ALIGNED / PG-0（限 PRD 与 Schema 核心）**，本评审人支持该拆轨方案。

## 4. ADVISORY

- **A-1（P2）**：STATUS.md 的更新仍在工作区未提交，而它是本申请交付物 #13。建议与 UC 修复一并提交，保持"申请范围 = 受审提交内容"。
- **A-2（P3）**：申请 §4 表第一行声称"通过全量字节扫描脚本验证"，脚本本体仍未入库（与第一轮 P3-1 同性质）；本评审人重放确认结论为真，仍建议将扫描落入 `tests/` 或 CI。

## 5. 复审验收标准（下一轮）

1. `2026-09-01-review-result-caf3473-qwen.md` §4 的 6 条验收断言全部通过（UC 修复）；
2. 本报告 §1 的 9 项无回退（抽样重放：控制字符扫描 + vote_result 反例拦截）；
3. 若拆轨：新申请文须显式声明交付物范围与排除项，STATUS.md 同步。

## 6. Reviewer 自审记录

- 第一轮（`2766c69`）本人投 APPROVE 时的 3 项登记（验证脚本未入库、Schema 双拷贝守卫、disposition 超时转移行）：前两项本轮以 ADVISORY 延续登记；第三项（disposition 超时转移行）在现行 `UC9:31-41` 与 PRD §6.2 已有超时降级路径承接，维持"实施期回补"级别，不升级；
- 本轮与平行 UseCases 评审为同基线独立出具，B-0 直接引用彼报告避免重复取证；两报告判定相互一致，无冲突；
- 未采信申请"100% 闭环"自述：§1 每项均附本机实测证据。
