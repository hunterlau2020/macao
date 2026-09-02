# MACAO PRD v2.5 架构方案、契约库与用例体系复审申请（Commit 4027cce）

- **申请日期**：2026-09-02
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（PRD v2.5 产品设计、契约库与用例体系全面对齐与实施准入）**
- **当前代码与文档基线**：`commit 4027cce`（`origin/main`）
- **前序受审基线与专家票型**：
  - `6e35a71`: Grok (`APPROVE`×2), Qwen (`APPROVE`×2), Claude (`NO_APPROVE`×2, P1×5/P1×4), Codex (`REJECT`, P1×8)
  - `5583bdd`: Grok (`NO_APPROVE`, P1×2: P1-1 E7 override exit edge, P1-2 D-1~D-9 table matching)
  - `caf3473`: Claude (`NO_APPROVE`, P1×5), Grok (`NO_APPROVE`, P1×3), Qwen (`NO_APPROVE`, BLOCKING×6)
- **上位评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**：[`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 评审背景与申请说明

针对专家委员会对上一轮提交 `6e35a71` 提出的全部阻断项（包括 Claude P1×5/P1×4、Codex P1×8），MACAO 架构团队已在 `4027cce` 实施了全量物理修复与自动化闭环验证：

1. **Schema 契约加固**：
   - `macao_config.schema.json` 根级强制 `policy` 与 `vote_weight`，封闭为 `weighted_2/3_v1`；
   - `dev_manifest.schema.json` 补齐 `task_id`、`checkpoint_ref`、`full_document` 根级必填；
   - `review_disposition.schema.json` 强制 `issues_index_sha256` 必填，`DEFERRED`/`REJECTED`/`EXEMPTED_BY_ADMIN` 与 `requires_new_checkpoint: false` 强联动互锁；
   - `aep_envelope.schema.json` 建立 per-type payload 校验（Type A/B/E/H）及 2048 字符文本预算限制；
   - 正例 **9/9 PASS**，反例 **13/13 100% 准确拦截（FAIL-CLOSED）**。
2. **PRD 与权威文档自洽**：
   - PRD §3.3 状态机表严格同步 E4 六关卡合并顺序与 E7 两步豁免流（`admin_override.json` $\rightarrow$ `SHOULD_DISPOSE` $\rightarrow$ 执行者 FINAL disposition $\rightarrow$ E4 `MERGING`）；
   - 变更清单严格互锁 E6 返工 commit 拓扑单调前进要求（`git merge-base --is-ancestor <prev> <new>`）。
3. **用例体系标准化**：
   - UC-7 剥离初始化歧义向导与 Git Conflict，收敛于 P1～P4 运行期触发；补齐标准 5～8 节（含设计自审）；
   - UC-6 补齐标准 5～8 节；UC-8 明确远端共享模式（`ls-remote` fail-closed）与纯本地模式边界。

---

## 2. 申请分轨入口索引

本轮评审申请包含两大专业分轨，评审专家可分别查阅对应分轨专项申请：

| 评审分轨 | 对应专项申请文件 | 待审核心交付物 | 核心核验重点 |
|---|---|---|---|
| **轨 1：PRD v2.5 设计同步轨** | [`2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-4027cce-PRD-v2.5-Design-Sync.md) | `docs/MACAO_PRD_v2.md`<br/>`docs/schemas/*.schema.json`<br/>`docs/PRD_CHANGE_PROPOSAL_v2.5.md`<br/>`docs/v2.5_CODE_CHANGE_INVENTORY.md` | D-1～D-9 架构裁定、不可变计票、单写者垄断、Draft-07 契约库、8 类 AEP 消息 |
| **轨 2：全量用例体系对齐轨** | [`2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-4027cce-UseCases-v2.5-Alignment.md) | `docs/usercases/`（13 份用例文档） | 100% 覆盖率、处置分流确定性（E4/E5a）、六道合并关卡、超时守护与既有项目诊断 |

---

## 3. 自动化机验结果

- **全库 Markdown 控制字符扫描**：188 份文档（`git ls-files "*.md"` 170 份，`docs/` 177 份）**0 控制字符（100% CLEAN）**；
- **Schema 契约双向一致性**：`docs/schemas/` ↔ `src/macao/schemas/` **8 份逐字节一致（0 diff）**；
- **Fixtures 双向门禁测试**：9 份正例 **9/9 PASS**，13 份反例 **13/13 100% 准确拦截**；
- **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 86 tests — 100% OK（86/86 PASS，0 Failures，0 Errors）**；
- **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 定级建议

全量技术方案、Schema 机器契约与用例体系已全面达成严密自洽并经自动化测试全项验证，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
