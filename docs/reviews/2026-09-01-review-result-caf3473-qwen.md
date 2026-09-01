# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`caf3473`）

- **评审日期**：2026-09-01
- **评审人**：`qwen`（独立评审；对 Claude/Grok 未提交报告的全部 BLOCKING 逐项独立复核，不直接采信）
- **评审对象**：`docs/reviews/2026-09-01-review-request-UseCases-v2.5-Alignment.md`；实际基线 **`caf3473`**（申请声明基线 `2c40cd5`，但 HEAD `caf3473` 又修改了交付物之一 `UC6`，以 HEAD 为准）
- **评审基准**：`docs/MACAO_PRD_v2.md`（v2.5）、`docs/schemas/*.schema.json`（Draft-07）、`docs/PRD_CHANGE_PROPOSAL_v2.5.md` §2 D-1~D-9 权威编号、`docs/usercases/PRODUCT-FACTS.md` F-1~F-22、GUIDELINES
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **机器票**：**`NO_APPROVE`**
- **结构化 issue**：`BLOCKING` × 6（含本评审人独立新发现 1 项）、`ADVISORY` × 3

---

## 1. 声明核验：通过的项（先列证据，避免只报问题）

| 申请声明 | 独立核验 | 判定 |
|---|---|---|
| 测试 86/86、compileall 0 错 | 本机重跑：`Ran 86 tests ... OK`（31.4s）；compileall 通过 | ✅ 真 |
| 13 份文档 0 控制字符 | 本机重放扫描命令：全部干净 | ✅ 真 |
| fixtures valid 8/8、invalid 100% 拦截 | 本机用 Draft7Validator 重放：8 正例全过；6 反例（含 `disposition_final_with_needs_admin`、`vote_result_cancelled_decision`、`context_missing_refs` 等）全部被拒 | ✅ 真 |
| `docs/schemas/` 与 `src/macao/schemas/` 0 diff | `diff -r` 实测零差异（除 fixtures/README/`__init__.py`） | ✅ 真 |
| UC-4 收敛条件 `accounted == configured` | `UC4-review-dispatch.md:48` | ✅ 真 |
| UC-3 拓扑单调前进 | `UC3-dev-checkpoint.md:16`（"严格为上轮 checkpoint_ref 之子孙且未被消费"） | ✅ 真 |
| UC-9 超时弃权计入 accounted、严格排除于 $E_N$/$E_W$、`source: "timeout"`、迟到票 `LATE_REVIEW_ISOLATED` | `UC9-timeout-daemon.md:31/36-41/51` | ✅ 真 |
| UC-5 五重门禁纯整数公式与 D-6 逐字一致 | `UC5-consensus-tally.md:30-36` vs 提案 :39 | ✅ 真 |
| UC-6 三态 + 100% 覆盖 + FINAL 禁 NEEDS_ADMIN + `requires_new_checkpoint` 布尔守卫 | `UC6-issue-triage-rework.md:35/58` + fixture 反例实测拦截 | ✅ 真 |
| UC-7 4 选项闭合 + `--exempt-issue-ids` + 原 vote_result 不可变 | `UC7-human-override.md:29/35-38/45` | ✅ 真 |
| UC-10 零侵入只读、不自动转移、独裁帽检查 | `UC10-existing-project-doctor.md:7/26-30` | ✅ 真 |
| `docs/usecases` 软链 | 实测 `docs/usecases -> usercases` | ✅ 真 |

## 2. BLOCKING（P1，任一项存在即不能授予 L1）

### B-1　处置产物路径三方分裂（独立复核确认 `claude/U-1`）

- **证据**：写者侧 `UC6-issue-triage-rework.md:24`、`README.md:97` 均为 **`.macao/executor.disposition.yml`**（扁平路径）；读取侧 `MACAO_PRD_v2.md:768`（Layer 1c 守卫）与 `:526/:561`（§2.5 示例）均为 **`.macao/.dispositions/r<round>/executor.disposition.yml`**。
- **后果**：照用例实现将写到守卫永不读取的路径 → `CONSENSUS_CHECK` 在 `APPROVED + requires_disposition` 分支永久静默 HOLD，无任何报错。
- **修正**：以 PRD Layer 1c 读取路径为唯一权威，回改 UC-6:24 与 README:97（含 archive 路径同步）。

### B-2　AEP Type 字母整体错位一位（独立复核确认 `claude/U-2`，且申请文自身带错）

- **证据**：PRD v1.1 类型表（`MACAO_PRD_v2.md:350-352`）：`DEVELOPMENT_STARTED`=**Type A**、`REVIEW_REQUEST`=**Type B**、`REVIEW_RESPONSE`=**Type C**；而 `UC2-task-create.md:51`、`UC4-review-dispatch.md:7`、`README.md:43/45/61/67` 及**申请 §2 表第 4/6 行**均写 DEVELOPMENT_STARTED=Type B、REVIEW_REQUEST=Type C——与 Type C=REVIEW_RESPONSE 直接冲突，用例集内部自相矛盾。
- **修正**：全量替换为 PRD 表字母；申请文 §2 表同改。

### B-3　`.review.yml` issue 列表字段名与机器契约不符（独立复核确认 `claude/U-3`）

- **证据**：`review_manifest.schema.json` 顶层属性为 `items`（实测无 `issues` 属性；正例 `fixtures/valid/review.yml` 用 `items` 通过）；`UC4-review-dispatch.md:40/81` 写 `issues[]` 且验收断言直接引用该错误字段名。
- **后果**：照 UC-4 验收标准写的断言永远失败；照其实现的 Adapter 输出必被 Schema 拒绝。
- **修正**：UC-4 `issues[]` → `items[]`（含 §6 验收断言）。

### B-4　UC-8 缺 Pre-merge Evidence Push 关卡且封存顺序倒置（独立复核确认 `claude/U-4`）

- **证据**：PRD §14.5 流水线第 1 关即"**Pre-merge Evidence Push 校验**（`ls-remote` 确认 evidence ref 已推远端）"，第 5 关才是源码 push + Post-merge Seal；`UC8-merge-signoff.md:19-37` 五道关卡无此关，且把 evidence 提升放在关卡 5 源码 push **之后**——与"评审证据先于源码合并封存"的两阶段语义相反。
- **修正**：UC-8 增加关卡 1.5（或重排为六关）：pre-merge `ls-remote` 校验 evidence ref；evidence 提升语义移至推送前。

### B-5　UC-3 示例与实现落点落后于契约；UC-1-gemini 整节停留 v2.4（独立复核确认 `claude/U-13`）

- **证据 A**：`dev_manifest.schema.json` 的 `full_document` **required = [path, evidence_commit, sha256]**；`UC3-dev-checkpoint.md` 的 yaml 示例 `full_document` 只有 path+sha256（缺必填 `evidence_commit`），且实现落点 `:104` 也只写 `{path,sha256}`。该示例过不了自家契约。
- **证据 B**：`UC1-init-gemini.md:127` `version: "2.4"`、`:162` `consensus_strategy: "majority"`——`macao_config.schema.json` 要求 `policy.consensus_rule ∈ {weighted_2/3_v1}`，按此生成的配置会被 Loader 拒绝。
- **修正**：UC-3 示例补 `evidence_commit` 并同步 :104；UC-1-gemini 配置规格升版或在文件头显式标注"v2.4 历史稿，以 UC-1-glm 为准"。

### B-6　申请 §3 的 D-1~D-9 编号与权威裁定表系统性错位（本评审人独立新发现）

- **权威编号**（`PRD_CHANGE_PROPOSAL_v2.5.md:34-42`）：D-2=**独立 disposition**、D-4=**DEFERRED 命名**、D-5=**requires_new_checkpoint 显式布尔**、D-6=**五重门禁**、D-8=**evidence ref**、D-9=**init/doctor/reconcile/adopt 职责**。
- **申请 §3 表**：D-2=admin override、D-3=disposition、D-4=三态收敛、D-5=五重门禁、D-6=FSM 三投影、D-8=checkpoint 拓扑、D-9=单写者命名——**至少 6 个编号与权威表不符**，且完全丢失权威 D-3（显式 ABSTAIN `source: manifest|timeout`）、D-4、D-9。
- **交叉引用已实际撕裂**：`PRODUCT-FACTS.md:47`（F-20）与 `UC1-init-glm.md:327` 按权威编号引用"disposition = D-2"；`UC7-human-override.md:5` 与申请 §2 表按申请编号引用"admin_override = D-2"。同一文档体系内 "D-2" 指向两个不同裁定。
- **后果**：该申请的核心交付物就是"D-1~D-9 对齐对照表"，表本身不可作为追溯依据；后续实现者按表找裁定会落到错误条目（如按申请 D-5 去实现五重门禁，查权威 D-5 却是 requires_new_checkpoint）。
- **修正**：申请 §3 表整体重排为提案权威编号，admin_override/FSM 投影/单写者命名等未编号主题改为无编号主题行或补录新裁定号；UC-7:5 的 D 引用同步澄清。

## 3. ADVISORY（P2/P3，不阻断但须登记）

- **A-1（P2）**：申请声明基线 `2c40cd5`，实际交付物在 `caf3473` 已再变更（UC-6）。基线声明必须等于实际受审 commit。
- **A-2（P3）**：申请 §5 称反例库覆盖"非法 `choice`"，但 `fixtures/invalid/` 无 `admin_override` 非法 choice 反例（现有 6 反例不含）；建议补一个。
- **A-3（P3）**：`UC6-issue-triage-rework.md:6` 边界声明引用 "F-13/F-16/F-21"——F-21 是三层审计事实，处置边界应引 F-20（D-1/D-2 锚点）；引用号建议更正。

## 4. 定级意见与验收标准

- 6 项 BLOCKING 中 5 项经本评审人独立复现确认（与 `2026-09-01-review-result-caf3473-claude.md` 的 U-1/U-2/U-3/U-4/U-13 一致），1 项（B-6）为本评审人独立发现；
- 用例正文对 v2.5 **语义**的对齐度实际很高（五重门禁、三态处置、单写者、超时边界全部逐字核验通过），缺陷集中在**路径/字段名/Type 字母/关卡顺序/示例版本/裁定编号**这类机器契约级细节——正是 L1 DOC-ALIGNED 判据所要求的"文档与机器契约一致"；
- **结论：`NO_APPROVE`，维持不定级**。修订上述 6 项后单提交复审（复审范围限于该 diff + 本报告验收项）：
  1. `grep -rn "executor.disposition" docs/usercases` 全部命中 `.macao/.dispositions/r<round>/` 前缀；
  2. `grep -rn "Type B.*DEVELOPMENT\|Type C.*REVIEW_REQUEST" docs/usercases docs/reviews/2026-09-01-review-request-UseCases-v2.5-Alignment.md` 零命中；
  3. UC-4 无 `issues[]` 残留；
  4. UC-8 含 pre-merge evidence `ls-remote` 关卡且 evidence 提升在源码 push 前；
  5. UC-3 示例过 `dev_manifest.schema.json`（可用 fixture 校验脚本复现）；UC-1-gemini 标注历史稿或升版；
  6. 申请 §3 表编号与提案 :34-42 逐条一致，"D-2" 全库仅指 disposition。

## 5. Reviewer 自审记录

- 全部 BLOCKING 均给出 `文件:行号` + 可复现命令/实测输出；对 Claude 报告的 5 项结论逐一独立复现后才引用，非转述；
- 对申请 §4 的 4 组自动化声明全部本机重放（测试/编译/控制字符/fixtures/schema diff），结果为真，已在 §1 如实记录，未因整体否决而抹杀；
- 利益声明：本评审人是 UC-1~UC-10 初稿作者（`4bc7bc0`），本轮缺陷多数产生于后续 v2.5 重对齐提交（`2c40cd5`/`caf3473`），判定以当前文本证据为准。
