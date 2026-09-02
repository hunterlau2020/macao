# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单复审申请（Commit cd285dd）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码与文档基线**：`commit cd285dd`（`origin/main`）
- **前序受审基线与票型**：
  - `a0123e8`: Claude (`NO_APPROVE`, P1×2), Codex (`REJECT`, P1×3), Grok (`NO_APPROVE`, P1×1), Qwen (`NO_APPROVE`, BLOCKING×3)
  - `4027cce`: Claude (`NO_APPROVE`), Codex (`REJECT`), Grok (`NO_APPROVE`), Qwen (`NO_APPROVE`)
  - `6e35a71`: Grok (`APPROVE`), Qwen (`APPROVE`), Claude (`NO_APPROVE`), Codex (`REJECT`)
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与核心修复

针对专家委员会对前序基线 `a0123e8` 指出的 3 项核心阻断项，团队在 `cd285dd` 落实了以下闭环：

1. **D-6 权重算术与独裁帽及法定人数配置期语义校验**：
   - `validate_config()` 与 `ConfigManager.load_config()` 实现全套 D-6 纯整数语义校验（独裁帽 $\forall i, 3 \times w_i < 2 \times W$、席位法定人数 $E_N \ge \lceil 2N/3 \rceil$、权重法定人数 $E_W \ge \lceil 2W/3 \rceil$、胜方席位上限 $2 \le \text{minimum\_winning\_seats} \le N$）；
   - 补充 `[5,1,1]` 违规权重、低 seat quorum、低 weight quorum 三份反例 fixtures 并在测试套件中 100% fail-closed 拦截。
2. **`vote_result_ref` 设为 `review_disposition` 强制必填契约**：
   - `review_disposition.schema.json` 顶层 `required` 纳入 `vote_result_ref`（`additionalProperties: false`）；
   - 提案 §4.2 示例与 fixture 同步补齐；新增缺失 `vote_result_ref` 的负例 fixture 并通过拒绝测试。
3. **E7 源状态统一收敛为 `HOLD (CONSENSUS_CHECK)`**：
   - 提案 §4.5 转移表修订（L226）与清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md`（L85）彻底清理“或 `REWORK`”残余；
   - 提案 L218 超时停驻态对齐为 `CONSENSUS_CHECK`。
4. **AEP 8 类封闭 Payload 契约与递归字节预算**：
   - 8 类 payload 明确 `additionalProperties: false`，Type E 补齐 6 项必填控制字段；
   - `AEPEnvelope.validate_budget()` 递归检查整信封 ≤16 KiB 与嵌套任意字段 ≤2048 字符。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：D-1～D-9 架构裁定、五重纯整数门禁、E7 两步 override、AEP/1.1 8 类消息、代码块示例 100% 过契约。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：8 份契约与 30 份 fixtures，强制反支配硬门禁、封闭 payload 与 `vote_result_ref` 必填约束。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：统一两步 override 规范与 E7 源态 `CONSENSUS_CHECK`。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐，E7 守卫与 PRD 权威表 100% 吻合。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 8 类 AEP 引用协议。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-1～F-22 全量作为设计约束。 |
| 8 | [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全量 126 份结论报告与 32 份申请。 |

---

## 3. 自动化验证结果

1. **PRD 全量代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors, 0 Warnings）**。
2. **全库文档控制字符扫描**：206 份 Markdown 文档 **0 控制字符（100% CLEAN）**。
3. **Schema 契约与 Fixtures 双向校验**：10 份正例 **10/10 PASS**，20 份反例 **20/20 准确拦截（FAIL-CLOSED）**；`docs/schemas/` 与 `src/macao/schemas/` **0 diff**。
4. **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 93 tests — 100% OK（93/93 PASS）**。
5. **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

设计同步轨的前序全部阻断项均已完成代码与文档级的物理闭环，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
