# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单复审申请（Commit 73576c5）

- **申请日期**：2026-09-03
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码与文档基线**：`commit 73576c5`（`origin/main`）
- **前序受审基线与票型（`cd285dd` 轮）**：
  - Claude (`NO_APPROVE`, P1×2), Codex (`REJECT`, P1×3), Grok (`NO_APPROVE`, P1×1), Qwen (`NO_APPROVE`, P1×1)
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与核心修复

针对专家委员会对前序基线 `cd285dd` 指出的阻断项，团队在 `73576c5` 落实了以下闭环：

1. **根 `macao.yaml` 策略 Quorum 与 D-6 运行时校验语义对齐（Grok P1-1 / Qwen P1-1 / Claude A-P1-2 / Codex P1-1）**：
   - 修复根 `macao.yaml` Quorum 参数，将 4 审查员团队的 `seat_quorum_required` 与 `weight_quorum_required` 正确设定为 `3`（满足 $\lceil 2 \times 4 / 3 \rceil = 3$ 门禁）；
   - `ConfigManager` 增加 `@property seat_quorum_required` 与 `@property weight_quorum_required`；
   - `tests/test_config.py` 增加 `test_root_macao_yaml_passes_semantic_validation`，验证根配置同时通过 Draft-07 Schema 与全套语义校验（10/10 PASS）。
2. **提案 §4.2 表格残余“当前状态（HOLD）”及链接规范化（Claude A-P1-1）**：
   - 彻底清理 `docs/PRD_CHANGE_PROPOSAL_v2.5.md` L128-129 残余表述，统一规范为 `` `CONSENSUS_CHECK`（HOLD） ``；
   - 将 L514 处绝对文件路径替换为相对路径 `MACAO_PRD_v2.md`。
3. **`review_disposition.schema.json` 顶层与嵌套全量封闭（Claude A-P2-3 / Codex P2-1）**：
   - 为根对象、`executor`、`full_document` 以及 `dispositions.items` 全量追加 `"additionalProperties": false`；
   - 增设反例 fixture `disposition_unrecognized_property.yml` 并在测试中验证精确拦截。
4. **`ConsensusEngine.evaluate()` 纯整数加权 2/3 五道门禁实装（Codex P1-1 / Claude A-P1-3）**：
   - 废除浮点数除法，重构为纯整数交叉乘法五道门禁；
   - 在 `tests/test_consensus.py` 中新增 Codex 反例测试 `test_weighted_counterexample_deadlock`（`[YES w=2, NO w=1, NO w=1]` 确凿产出 `DEADLOCK`）与 `test_weighted_minimum_winning_seats_enforcement`。
5. **`vote_result.schema.json` 契约强化与生成器对齐（Claude A-P1-3, A-P1-5 / Codex P1-3）**：
   - Schema 强制要求 `generated_at`、`task_id`、`executor_id`，封闭对象（`additionalProperties: false`），`resolution` 枚举收敛为 `["AUTO_WEIGHTED_CONSENSUS", "HUMAN_OVERRIDE"]`；
   - `vote.py` 补充 `source`（`manifest` / `timeout`）与 `weight`；
   - 精确区分 `reviewers_responded`（manifest 提交数）与 `reviewers_accounted`（含超时总数）；
   - `issues_index_sha256` 实时计算真实 SHA-256 哈希；新增反例 fixture `vote_result_missing_source.json` 并拦截。
6. **编排器 E4 守卫与 Type E `DISPOSITION_REQUIRED` 发布（Claude A-P1-4 / Codex P1-2）**：
   - `Orchestrator.collect_and_evaluate_consensus`：当 `APPROVED` 且存在 issues 时，严禁直跳 `MERGING`，必须停驻于 `CONSENSUS_CHECK` 并发布 Type E `DISPOSITION_REQUIRED`；
   - 增加 `submit_disposition()` 接口与 E5a 返工转移；仅当存在合法 FINAL disposition 且所有项目 `requires_new_checkpoint == False` 时才允许 E4 转移至 `MERGING`；
   - 在 `tests/test_p0_p1_rectification.py` 中新增集成测试 `test_approved_with_advisory_holds_and_requires_disposition`。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：D-1～D-9 架构裁定、五重纯整数门禁、E7 两步 override、AEP/1.1 8 类消息、代码块示例 100% 过契约。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：8 份契约与 32 份 fixtures，强制反支配硬门禁、封闭 payload 与 `vote_result_ref` 必填约束。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：统一两步 override 规范与 E7 源态 `CONSENSUS_CHECK`，清理残余表述。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐，E7 守卫与 PRD 权威表 100% 吻合。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 8 类 AEP 引用协议。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-1～F-22 全量作为设计约束。 |
| 8 | [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全量 136 份结论报告与 35 份申请。 |

---

## 3. 自动化验证结果

1. **PRD 全量代码块 Draft-07 Schema 校验**：`tests/test_prd_snippets_schema.py` **100% PASS（0 Errors, 0 Warnings）**。
2. **根配置语义与 Schema 校验**：`tests/test_config.py` **10/10 PASS**。
3. **加权计票五门禁与反例推导**：`tests/test_consensus.py` **5/5 PASS**。
4. **全库文档控制字符扫描**：212 份 Markdown 文档 **0 控制字符（100% CLEAN）**。
5. **Schema 契约与 Fixtures 双向校验**：10 份正例 **10/10 PASS**，22 份反例 **22/22 准确拦截（FAIL-CLOSED）**；`docs/schemas/` 与 `src/macao/schemas/` **0 diff**。
6. **全套单元与回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 97 tests — 100% OK（97/97 PASS）**。
7. **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

设计同步轨的前序全部阻断项均已完成代码、契约与文档级的物理闭环并接入测试门禁，提请专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
