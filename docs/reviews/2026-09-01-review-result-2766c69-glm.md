# PRD v2.5 Design-Sync 终局定级复核（L1 / PG-0）评审结论

- **评审日期**：2026-09-01
- **评审对象**：评审申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`；交付物基线 commit `2766c69`（闭环提交）及其声称修复的 `0bc6247` 五方专家全部阻断项
- **评审人**：glm（独立评审，全部关键声明逐项机验取证）
- **结论**：**APPROVE —— 授予 L1 DOC-ALIGNED / PG-0（文档基线定级与技术准入）**，附 3 项非阻断登记项（P3/P2，不阻塞 Phase 1 启动）

---

## 1. 声明逐项核验表（全部独立复核，非采信自述）

| # | 申请声明 | 独立核验证据 | 判定 |
|---|---|---|---|
| 1 | Layer 1b 废除 `minimum_quorum` 提前返回 | `MACAO_PRD_v2.md:751-756`：`accounted == configured` 后才转移，无 quorum 截断残留 | ✅ VERIFIED |
| 2 | Layer 1c 补 DEADLOCK HOLD / requires_disposition / E5a，移除机器决定 RETRY_REVIEW/CANCELLED | `MACAO_PRD_v2.md:758-789`：三分支 + disposition FINAL 校验 + `requires_new_checkpoint` 布尔驱动 E5a/E4；REWORK 超限走 `request_human_override`（命令型，非机器决定） | ✅ VERIFIED |
| 3 | 场景三 DEADLOCK 即时落盘不可变 vote_result + 独立 admin_override，严禁二次回写 | `MACAO_PRD_v2.md:884-886`（Step5 即时落盘 → Step6 admin_override.json）；E3 行（:825）同口径；:17 计分只读声明 | ✅ VERIFIED |
| 4 | `review_context` 嵌套 `refs: {base_commit, head_commit}` | Schema 实测：`review_context.schema.json` 含 `refs/base_commit/head_commit`；PRD §5.2 示例（:1001 `refs:`） | ✅ VERIFIED |
| 5 | `vote_result` 含 `policy_snapshot` + 整数计票 | Schema 实测：`policy_snapshot`/`weight`/`issues_index`/`requires_disposition` 均在；PRD :296-309 整数 seat/weight 计数示例 | ✅ VERIFIED |
| 6 | `review_manifest` 五重条件互锁 | **独立构造 6 个用例实测**：BLOCKING+YES 拒 ❌、BLOCKING+NO 过 ✅、ABSTAIN 缺理由拒 ❌、ABSTAIN 带理由带 items 拒 ❌、ABSTAIN 合法过 ✅、干净 YES 过 ✅——与申请"5/5 PASS"一致 | ✅ VERIFIED |
| 7 | 新增 `review_disposition.schema.json` / `admin_override.schema.json` | 两文件在 `docs/schemas/` 与 `src/macao/schemas/`，Draft7Validator.check_schema 通过；`requires_new_checkpoint` / 豁免字段在位 | ✅ VERIFIED |
| 8 | PRD §2.5 `executor.disposition.yml` 规范 | :18/:112/:526/:561 及 §2.5 代码块（:536 起） | ✅ VERIFIED |
| 9 | AEP/1.1 8 类消息 + Type E 示例 + 无 base64 + 16 KiB/2048 预算 | :354（Type E 表行）、:535-543（完整 JSON 示例）、全文 `grep -c base64` = 0、:360（16384/2048） | ✅ VERIFIED |
| 10 | §14.3~14.5 与第十五部分恢复无死链 | :1442/1446/1450/1465-1489（15.1~15.5 全在），E4 行交叉引用 §14.5 有效 | ✅ VERIFIED |
| 11 | 代码清单与模块树对齐 | 逐路径核对：`fsm.py`/`controller.py`/`main.py`/`wizard.py` 均实际存在，`storage/evidence.py` 明确标注新建 | ✅ VERIFIED |
| 12 | UC-1/5/6/7/8/9 同步 + PRODUCT-FACTS F-20 | UC-6（0bc6247 已改）：`executor.disposition.yml` + 100% 覆盖率 + `requires_new_checkpoint` + E5a；F-20 记录"由 PRD v2.5 D-1/D-2 显式裁定落实" | ✅ VERIFIED |
| 13 | 测试 84/84 + compileall 0 错 | 本机实测：`Ran 84 tests ... OK`（38.7s）；compileall 通过 | ✅ VERIFIED |

## 2. 历史遗留问题的闭环确认（本 reviewer 前轮提出项）

| 前轮问题（评审人 glm） | 本轮处置 | 判定 |
|---|---|---|
| P0-1：F-13/F-16"汇总段写入 vote_result"被提案无声推翻 | 提案 v0.3 **D-1/D-2 显式裁定**："正式替代旧 FAQ/UC 中 Executor 回写 `vote_result.issues_summary` 的双写者方案"，并落锚 PRODUCT-FACTS **F-20**；UC-5/UC-6 已同步改写，无残余双写者表述 | ✅ 已按程序闭环（显式裁定 + 事实源锚定 + 下游同步，正是当时要求的最低修正） |
| P1-1：ABSTAIN 与已实现三值行为冲突且迁移缺失 | PRD :234 `vote` 枚举含 ABSTAIN，:236 显式弃权必填 `abstain_reason` 且 items 必空；Schema 互锁 + `test_phase3.py` 补弃权理由断言——与现行代码三值闭环一致 | ✅ 已裁决为保留显式弃权通道 |
| P2-1：处置穷尽性放宽未声明 | E4 守卫（:827）"**精确覆盖全部 issue**"；UC-6 边界声明"覆盖率 100%"——恢复全穷尽 | ✅ 已收紧 |

## 3. 非阻断登记项（不阻塞 L1/PG-0）

- **P3-1　验证脚本未入库**：申请 §4 的"脚本 1/2/3"为一次性验证，未提交为可复现测试（`docs/schemas/fixtures/` 有 valid/invalid 目录但无 `review_manifest_valid.json` 等同名 fixture；本轮互锁结论由本 reviewer 独立重放得出，声明为真但仓库内不可复现）。建议 Phase 1 前把 Schema 互锁测试落入 `tests/`（fixtures 已具备）。
- **P3-2　Schema 双份拷贝漂移风险**：`docs/schemas/` 与 `src/macao/schemas/` 内容当前一致（diff 仅 fixtures/README/`__init__.py`），但无同步校验。建议在 CI 或测试中加 `diff -r` 守卫，防止单边演进。
- **P2-1　disposition 超时治理**：STATUS.md 轮次 66 记录 Kimi 曾提"disposition 超时"加固项；本轮 PRD 的 `CONSENSUS & DISPOSITION` 行给出场时限（30m），但超时后的转移（继续 HOLD→人工接管？）在 §3.3/§6 未见显式行。属实施期（Phase 5 disposition 守卫）必须补齐项，登记跟踪。

## 4. 定级意见

- 本轮申请属**文档基线定级（L1 DOC-ALIGNED）与技术准入（PG-0）**，不是运行时定级：所有核验对象为文档/Schema/既有测试回归，符合 GUIDELINES 对 L1 的判据；
- 五方专家在 `0bc6247` 提出的全部阻断项经本轮独立复核**逐项物理闭环**，无"声明修复、实际残留"项；
- 申请 §4 的自述验证结果与独立重放一致，无夸大；
- 同意授予 **L1 DOC-ALIGNED / PG-0**，批准启动 Phase 1~5；P2-1（disposition 超时转移行）须在 Phase 5 实现前回补进 PRD §3.3。

## 5. Reviewer 自审记录

- 按五项自检执行：本报告全部判定均有可复现命令/行号锚点；对申请自述的"100% PASS"未直接采信，互锁与测试均为本机重放；
- 声明利益关联：本 reviewer 是前轮提案评审（P0-1/P1-1/P2-1 提出者），本轮对三项的闭环判定基于文本与 Schema 证据，非因出处偏爱。
