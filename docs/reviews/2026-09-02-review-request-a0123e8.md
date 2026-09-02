# MACAO PRD v2.5 架构方案、契约库与用例体系复审申请（Commit a0123e8）

- **申请日期**：2026-09-02
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（PRD v2.5 产品设计、契约库与用例体系全面对齐与实施准入）**
- **当前代码与文档基线**：`commit a0123e8`（`origin/main`）
- **前序受审基线与专家票型**：
  - `4027cce`: Claude (`NO_APPROVE`, P1×5), Codex (`REJECT`, P1×5), Grok (`NO_APPROVE`, P1×2), Qwen (`NO_APPROVE`, DS-P1×5, UC-P1×2)
  - `6e35a71`: Grok (`APPROVE`×2), Qwen (`APPROVE`×2), Claude (`NO_APPROVE`×2, P1×5/P1×4), Codex (`REJECT`, P1×8)
  - `5583bdd`: Grok (`NO_APPROVE`, P1×2: P1-1 E7 override exit edge, P1-2 D-1~D-9 table matching)
  - `caf3473`: Claude (`NO_APPROVE`, P1×5), Grok (`NO_APPROVE`, P1×3), Qwen (`NO_APPROVE`, BLOCKING×6)
- **上位评审方法论**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)
- **实时门禁状态表**：[`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 评审背景与申请说明

针对专家委员会对上一轮提交 `4027cce` 提出的全部阻断项（四方独立收敛的 5 项核心 P1 阻断），MACAO 架构团队已在 `a0123e8` 实施了全量物理修复、Schema 契约收紧与自动化闭环验证：

1. **UC-8 纯本地模式 `remote_name: null` 全链路支持（阻断项 1）**：
   - `macao_config.schema.json` 与 `review_context.schema.json` 中 `remote_name` 更新为 `{"type": ["string", "null"]}`；
   - 增加合法测试 fixture `macao_config_local_only.yaml` 并全量机验通过；
   - PRD §14.5 Gate 1 正式补齐远端共享模式（`ls-remote` fail-closed）与纯本地模式（强校验本地 evidence ref，跳过远端推送）的双轨流水线。
2. **PRD 正式示例与 Draft-07 Schema 100% 校验对齐（阻断项 2）**：
   - 编写并固化全量 PRD 示例自动化校验门禁 `tests/test_prd_snippets_schema.py`；
   - PRD §2.4 AEP 示例（Type A 补齐 `specification_summary`/`acceptance_criteria`，Type B 补齐 10 大 context 语义块，Type E 补齐 `vote_result_ref`/`timeout_deadline`）；
   - PRD §2.5 `executor.disposition.yml` 补齐 `issues_index_sha256` 与 `vote_result_ref`；
   - PRD 第十三部分与仓库根 `macao.yaml` 补齐 `version: "2.5"`、`vote_weight: 1`、完整 `policy` 门禁块，`validate_config()` 机验 100% PASS。
3. **D-6 反支配门禁 Schema 硬约束（阻断项 3）**：
   - `macao_config.schema.json` 与 `vote_result.schema.json` 中 `minimum_winning_seats` 设为 `{"type": "integer", "minimum": 2}`；
   - `dictator_cap_enabled` 设为 `{"type": "boolean", "const": true}`；
   - 彻底删除孤儿冗余字段 `min_effective_votes`，统一以 `seat_quorum_required` 为唯一标准；
   - 新增针对单席位通过与禁用独裁帽的非法反例 fixture，机验 100% 拦截。
4. **E7 源态收敛与状态机统一（阻断项 4）**：
   - PRD §3.3 转移表与状态说明将 E7 源状态精准固化为 `HOLD (CONSENSUS_CHECK)`；
   - `PRD_CHANGE_PROPOSAL_v2.5.md` 第 135 行彻底清理“直接推进至 MERGING”陈旧文本，严格统一为管理员 override $\rightarrow$ 执行者提交 FINAL disposition $\rightarrow$ E4 `MERGING` / E5a `REWORK` 两步流。
5. **AEP 16 KiB 字节预算与 8 类封闭 Payload 契约（阻断项 5）**：
   - `aep_envelope.schema.json` 针对全部 8 类消息定义封闭 payload subschema 与 2048 字符文本字段上限；
   - Python 代码层 `AEPType` 枚举补充 `DISPOSITION_REQUIRED`（8 类全齐），`AEPEnvelope` 升级为 `AEP/1.1` 并内置 16 KiB / 2048 字节预算运行时校验。

---

## 2. 申请分轨入口索引

本轮评审申请包含两大专业分轨：

| 评审分轨 | 对应专项申请文件 | 待审核心交付物 | 核心核验重点 |
|---|---|---|---|
| **轨 1：PRD v2.5 设计同步轨** | [`2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md`](2026-09-02-review-request-a0123e8-PRD-v2.5-Design-Sync.md) | `docs/MACAO_PRD_v2.md`<br/>`docs/schemas/*.schema.json`<br/>`docs/PRD_CHANGE_PROPOSAL_v2.5.md`<br/>`docs/v2.5_CODE_CHANGE_INVENTORY.md` | D-1～D-9 架构裁定、不可变计票、单写者垄断、Draft-07 契约库、8 类 AEP 消息、PRD 示例 0 错误 |
| **轨 2：全量用例体系对齐轨** | [`2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md`](2026-09-02-review-request-a0123e8-UseCases-v2.5-Alignment.md) | `docs/usercases/`（13 份用例文档） | 100% 覆盖率、处置分流确定性（E4/E5a）、六道合并关卡、纯本地模式与超时守护 |

---

## 3. 自动化机验结果

- **全量 PRD 示例 Schema 契约校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors）**；
- **全库 Markdown 控制字符扫描**：188 份文档 **0 控制字符（100% CLEAN）**；
- **Schema 契约双向一致性**：`docs/schemas/` ↔ `src/macao/schemas/` **8 份逐字节一致（0 diff）**；
- **Fixtures 双向门禁测试**：10 份正例 **10/10 PASS**，16 份反例 **16/16 100% 准确拦截（FAIL-CLOSED）**；
- **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 92 tests — 100% OK（92/92 PASS，0 Failures，0 Errors）**；
- **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**；
- **`STATUS.md` 双向对账**：29 份申请与 120 份结论报告 **100% 双向对齐（0 遗漏）**。

---

## 4. 定级建议

全量 5 项跨专家 P1 阻断已彻底解决，全量 PRD 代码示例、契约库与测试套件达成机器自洽，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
