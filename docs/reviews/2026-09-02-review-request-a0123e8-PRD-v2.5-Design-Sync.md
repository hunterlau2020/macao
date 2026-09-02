# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单复审申请（Commit a0123e8）

- **申请日期**：2026-09-02
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码与文档基线**：`commit a0123e8`（`origin/main`）
- **前序受审基线与票型**：
  - `4027cce`: Claude (`NO_APPROVE`, P1×4), Codex (`REJECT`, P1×5), Grok (`NO_APPROVE`, P1×2), Qwen (`NO_APPROVE`, BLOCKING×5)
  - `6e35a71`: Grok (`APPROVE`), Qwen (`APPROVE`), Claude (`NO_APPROVE`, P1×5), Codex (`REJECT`, P1×8)
  - `5583bdd`: Grok (`NO_APPROVE`, P1×2)
  - `caf3473`: Claude (`NO_APPROVE`), Grok (`NO_APPROVE`), Qwen (`NO_APPROVE`)
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 专家意见闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与核心修复

针对专家委员会对上一轮提交 `4027cce` 指出的全部 Schema 与 PRD 核心阻断项，团队在 `a0123e8` 落实了以下闭环：

1. **PRD 示例 × Schema 契约 100% 校验通过**：
   - 固化 `tests/test_prd_snippets_schema.py` 自动化测试；
   - §2.4 Type A/B/E JSON 信封补齐必填字段与 10 大 context 块；
   - §2.5 `executor.disposition.yml` 补齐 `issues_index_sha256` 与 `vote_result_ref`；
   - 第十三部分 `macao.yaml` 与仓库根配置补齐 `version: "2.5"`、`vote_weight: 1` 与完整 policy 块。
2. **D-6 反支配门禁 Schema 物理锁死**：
   - `macao_config.schema.json` 与 `vote_result.schema.json` 强制 `minimum_winning_seats: {"minimum": 2}` 与 `dictator_cap_enabled: {"const": true}`；
   - 移除冗余字段 `min_effective_votes`，由 `seat_quorum_required` 充当唯一事实源。
3. **E7 源态精准固化为 `HOLD (CONSENSUS_CHECK)`**：
   - PRD §3.3 状态机表与提案彻底清理“直接推进至 MERGING”的违规路径，严格落实两步 override 规范。
4. **AEP 16 KiB / 2048 字节预算与 8 类封闭 Payload**：
   - `aep_envelope.schema.json` 封闭 8 类消息结构；
   - `AEPType` 枚举补充 `DISPOSITION_REQUIRED`，`AEPEnvelope` 升级为 `AEP/1.1` 并内置预算运行时校验。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：融入 D-1～D-9 架构裁定、不可变 `vote_result.json`、§2.5 `executor.disposition.yml`、加权纯整数五重门禁、AEP/1.1 全部 8 类消息、PRD 正式示例 100% 通过契约校验。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：完整提供 8 份契约与 26 份 fixtures，强制反支配硬门禁与字节预算。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：统一两步 override 规范与 10 大 context 语义块。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 8 类 AEP 引用协议。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-1～F-22 全量作为设计约束。 |
| 8 | [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全量 120 份结论报告与 29 份申请。 |

---

## 3. 自动化验证结果

1. **PRD 全量代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors）**。
2. **全库文档控制字符扫描**：188 份 Markdown 文档 **0 控制字符（100% CLEAN）**。
3. **Schema 契约与 Fixtures 双向校验**：10 份正例 **10/10 PASS**，16 份反例 **16/16 准确拦截（FAIL-CLOSED）**；`docs/schemas/` 与 `src/macao/schemas/` **0 diff**。
4. **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 92 tests — 100% OK（92/92 PASS）**。
5. **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

PRD v2.5 方案与全量技术设计文档、Schema 契约库达成机器级严密自洽，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
