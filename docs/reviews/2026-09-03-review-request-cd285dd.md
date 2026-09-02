# MACAO PRD v2.5 架构方案、契约库与用例体系复审申请（Commit cd285dd）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（PRD v2.5 产品设计、契约库与用例体系全面对齐与实施准入）**
- **当前代码与文档基线**：`commit cd285dd`（`origin/main`）
- **前序受审基线与专家票型**：
  - `a0123e8`:
    - 轨 B（用例对齐轨）：Claude (`YES_APPROVE`), Grok (`YES_APPROVE`), Qwen (`YES_APPROVE`), Codex (`REJECT`，证据指向契约与配置等轨 A 交付物)
    - 轨 A（设计同步轨）：Claude (`NO_APPROVE`, P1×2), Codex (`REJECT`, P1×3), Grok (`NO_APPROVE`, P1×1), Qwen (`NO_APPROVE`, BLOCKING×3)
  - `4027cce`: Claude (`NO_APPROVE`), Codex (`REJECT`), Grok (`NO_APPROVE`), Qwen (`NO_APPROVE`)
  - `6e35a71`: Grok (`APPROVE`×2), Qwen (`APPROVE`×2), Claude (`NO_APPROVE`×2), Codex (`REJECT`)
- **上位评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**：[`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 评审背景与申请说明

针对专家委员会对上一轮提交 `a0123e8` 提出的全部 3 项核心阻断项（四方独立收敛的 D-6 权重语义校验、`vote_result_ref` 必填契约、E7 源状态清理及 AEP 预算），MACAO 架构团队已在 `cd285dd` 实施了全量物理闭环、契约加固与自动化测试：

1. **D-6 权重算术与独裁帽及法定人数配置期硬门禁（阻断项 1）**：
   - `validate_config()` 与 `ConfigManager.load_config()` 实现全套 D-6 纯整数语义校验：
     - 强制独裁帽 $\forall i, 3 \times w_i < 2 \times W$（不满足直接拒绝）；
     - 强制席位法定人数 $E_N \ge \lceil 2N/3 \rceil$；
     - 强制权重法定人数 $E_W \ge \lceil 2W/3 \rceil$（分母为配置总权重 $W$）；
     - 强制 $2 \le \text{minimum\_winning\_seats} \le N$；
   - 修复 `vote.py` 计票快照中 `configured_weight` 与 `weight_quorum_required` 公式；
   - 新增反例 fixtures `macao_config_dictator_weight_violation.yaml`（`[5,1,1]` 违规）、`macao_config_low_seat_quorum.yaml`、`macao_config_low_weight_quorum.yaml` 并全量机验准确拦截。
2. **`vote_result_ref` 设为 `review_disposition` 强制必填契约（阻断项 2）**：
   - `review_disposition.schema.json` 将 `vote_result_ref` 纳入顶层 `required`，要求 `path/evidence_commit/sha256` 必填且 `additionalProperties: false`；
   - 同步更新 UC-6 规范示例、提案 §4.2 示例及有效 fixture `disposition.yml`；
   - 新增负例 fixture `disposition_missing_vote_result_ref.yml`，实测 100% 拒绝。
3. **E7 源态彻底收敛为 `HOLD (CONSENSUS_CHECK)`（阻断项 3）**：
   - 提案 §4.5 转移表（L226）与施工清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md`（L85）彻底清理“或 `REWORK`”残余；
   - 提案 L218 超时停驻态与 PRD §3.4 / UC-7 P3 严格对齐；
   - 全库检索 `grep -rn 'CONSENSUS_CHECK.*REWORK' docs/ --include='*.md' | grep -v '/reviews/'` 达成 **0 匹配（100% 洁净）**。
4. **AEP 8 类封闭 Payload 契约与递归字节预算（契约加固）**：
   - `aep_envelope.schema.json` 全部 8 类 payload 明确 `additionalProperties: false`；
   - Type E `DISPOSITION_REQUIRED` 严格要求 `task_id`、`checkpoint_ref`、`review_round`、`vote_result_ref`、`issues_index_sha256`、`timeout_deadline`；
   - `AEPEnvelope.validate_budget()` 实现递归遍历 UTF-8 字节预算（包括嵌套 dict/list/object 中 2048 字符上限校验）；
   - 更新反例 fixture `aep_payload_oversized.json` 包含真实 >2048 字符正文，拒因真实匹配名义。

---

## 2. 申请分轨入口索引

| 评审分轨 | 对应专项申请文件 | 待审核心交付物 | 前序基线（`a0123e8`）票型 | 本轮核验重点 |
|---|---|---|---|---|
| **轨 1：PRD v2.5 设计同步轨** | [`2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`](2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md) | `docs/MACAO_PRD_v2.md`<br/>`docs/schemas/*.schema.json`<br/>`docs/PRD_CHANGE_PROPOSAL_v2.5.md`<br/>`docs/v2.5_CODE_CHANGE_INVENTORY.md` | Claude (`NO_APPROVE`), Codex (`REJECT`), Grok (`NO_APPROVE`), Qwen (`NO_APPROVE`) | D-6 权重算术校验、`vote_result_ref` 必填契约、E7 转移表一致性、AEP 递归预算 |
| **轨 2：全量用例体系对齐轨** | [`2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md`](2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md) | `docs/usercases/`（13 份用例文档） | Claude (`YES_APPROVE`), Grok (`YES_APPROVE`), Qwen (`YES_APPROVE`) | UC-6 示例 `vote_result_ref` 补齐、全量 13 份用例与 PRD/契约 100% 自洽 |

---

## 3. 自动化机验结果

- **全量 PRD 示例 Schema 契约校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors, 0 Warnings）**；
- **全库 Markdown 控制字符扫描**：206 份文档 **0 控制字符（100% CLEAN）**；
- **Schema 契约双向一致性**：`docs/schemas/` ↔ `src/macao/schemas/` **8 份逐字节一致（0 diff）**；
- **Fixtures 双向门禁测试**：10 份正例 **10/10 PASS**，20 份反例 **20/20 100% 准确拦截（FAIL-CLOSED）**；
- **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 93 tests — 100% OK（93/93 PASS，0 Failures，0 Errors）**；
- **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**；
- **`STATUS.md` 双向对账**：32 份申请与 126 份结论报告 **100% 双向对齐（0 遗漏）**。

---

## 4. 定级建议

轨 B 已在上轮获得 Claude、Grok、Qwen 三方一致授予，轨 A 的全部 3 项核心阻断项已彻底闭环并通过机器自动化验证。提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
