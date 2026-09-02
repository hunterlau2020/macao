# 全量用例体系（UseCases）PRD v2.5 对齐复审（Round 2，`6e35a71`）评审结论

- **评审日期**：2026-09-02
- **评审对象**：`docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md`；实际基线 **`6e35a71`**（与申请声明一致；HEAD `12a05e2` 仅追加申请文件本身，非交付物）
- **评审人**：`qwen`（独立评审；本人为 `caf3473` 轮 NO_APPROVE（6 项 BLOCKING）的出具者，本轮为其修复后复审，逐项机验）
- **机器票**：**`YES_APPROVE`**
- **定级结论**：**L1 DOC-ALIGNED / PG-0（用例文档体系）**

---

## 1. 前序阻断项闭环核验（逐项机验）

### 1.1 本人 `caf3473` 轮 6 项 BLOCKING（`2026-09-01-review-result-caf3473-qwen.md`）

| # | 问题 | 修复核验 | 判定 |
|---|---|---|---|
| B-1 | disposition 路径分裂 | `UC6-issue-triage-rework.md:24/75`、`README.md:47/73/97` 全部为权威路径 `.macao/.dispositions/r<round>/executor.disposition.yml`；全库已无扁平路径断言（残留命中均为产物名泛指） | ✅ CLOSED |
| B-2 | AEP Type 字母错位 | `UC2-task-create.md:51` 现为 Type A、`UC4-review-dispatch.md:7`/README 现为 Type B；错误映射 grep 零命中 | ✅ CLOSED |
| B-3 | `issues[]` vs `items[]` | 全用例库 `issues[]` 零残留；`items[]` 契约与 `review_manifest.schema.json` 一致 | ✅ CLOSED |
| B-4 | UC-8 缺 Pre-merge Evidence 关卡且顺序倒置 | `UC8-merge-signoff.md` 现为**六关卡**：关卡 1 = Pre-merge Evidence Push 校验（`git ls-remote`，fail-closed 拦截，`:21-23`），源码推送在关卡 6；新增 `E4a_pre` 失败行（`:65`）与验收断言（`:76-77`） | ✅ CLOSED |
| B-5 | UC-3 示例缺 `evidence_commit`；UC-1-gemini 停留 v2.4 | 本机用 Draft-07 实跑：UC-3 yaml 块过 `dev_manifest.schema.json`（含 `evidence_commit`）；UC-1-gemini 配置块现为 `version: 2.5` + `weighted_2/3_v1`，过 `macao_config.schema.json` | ✅ CLOSED |
| B-6 | D-1~D-9 编号错位 | 本轮申请 §3 表与权威提案 `:34-42` 逐条一致（D-2=disposition、D-4=DEFERRED、D-5=requires_new_checkpoint、D-6=五重门禁、D-8=evidence ref、D-9=职责边界）；`F-20`、`UC1-init-glm.md:312`、`UC7-human-override.md:5` 的 D-1/D-2 引用全库一致，无交叉撕裂 | ✅ CLOSED |

### 1.2 Grok `5583bdd` 轮 2 项阻断

| # | 问题 | 修复核验 | 判定 |
|---|---|---|---|
| P1-1 | E7 豁免流出口边 | `UC7-human-override.md:35`：APPROVED → 落盘 `admin_override.json` + 投影 `SHOULD_DISPOSE` → 执行者提交 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL disposition → 校验通过后触发 E4；明文"**严禁无 FINAL 直跳 MERGING，严禁管理员代写 disposition**"；`UC1-init-glm.md:145-146` 投影表同步 | ✅ CLOSED |
| P1-2 | D-1~D-9 对照表 | 同 B-6 | ✅ CLOSED |

## 2. 申请 §4 自动化声明复核

| 声明 | 本机重放 | 判定 |
|---|---|---|
| 13 份文档 0 控制字符 | `docs/**/*.md` 全库扫描 181 份均 0（含用例 13 份） | ✅ |
| UC-6/UC-3/UC-1-gemini 示例过 Draft-07 | 三块全部实测 **PASS** | ✅ |
| fixtures valid 8/8、invalid 7/7 拦截 | 实测 8/8 + **7/7**（新增 `admin_override_invalid_choice.json` 反例——本人 `caf3473` 轮 ADVISORY A-2 已被采纳，实测被拒） | ✅ |
| `docs/schemas/` vs `src/macao/schemas/` 0 diff | 实测零差异（仅 `__pycache__`/`fixtures`/README 非契约文件） | ✅ |
| 86/86 测试、compileall 0 错 | 实测 `OK` + `0 Errors` | ✅ |

## 3. 深度抽查（防修复引入新矛盾）

- **UC-7 APPROVED 路径与 PRD §3.3 互锁**：PRD `§3.3` E4 条件现为"无 issue，或存在 FINAL disposition 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false`"；Layer 1c 伪码对 DEADLOCK+override APPROVED 分支：无 FINAL → 保持 HOLD（等处置），有 FINAL 按 `requires_new_checkpoint` 分流 E4/E5a——与 UC-7:35、UC-1:145-146、UC-6:75 三方一致，无直跳路径；
- **UC-8 六关卡顺序与 §14.5 一致**（pre-merge evidence → 检出 → 合并 → CI → 签字 → push+归档）；
- **单写者垄断**：`vote_result.json`（编排器）/`admin_override.json`（管理员）/`executor.disposition.yml`（执行者）在 13 份文档中写者归属无冲突，"代写"字样仅出现在禁令中；
- **软链** `docs/usecases -> usercases` 实测存在。

## 4. ADVISORY（不阻断）

- **A-1（P3）**：申请 §4.1 称扫描范围为 13 份用例文档，Design-Sync r2 申请称 179 份——实测全库 181 份；计数漂移，结论（0 控制字符）本身为真。
- **A-2（P3）**：扫描脚本仍为申请文内联命令，未落入 `tests/` 或 CI；建议实施期固化（延续前轮登记）。

## 5. 定级意见

6 + 2 项前序阻断全部物理闭环、无回退；修复未引入新矛盾；申请 §4 五组自动化声明全部重放为真。

**结论：授予 `L1 DOC-ALIGNED / PG-0`**，用例体系可自本基线起作为 Phase 1~5 的官方操作基准。

## 6. Reviewer 自审记录

- 本人为 `caf3473` 轮阻断项出具者，本轮全部修复均重新取证（未以"已按我清单修复"为由直接放行）；
- 对申请自述的每一项自动化结论均本机重放；
- 利益声明：本评审人系 `UC-1~UC-10` 初稿作者（`4bc7bc0`），本轮判定仅以 `6e35a71` 文本证据为准。
