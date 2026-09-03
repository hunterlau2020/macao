# 全量用例体系（UseCases）PRD v2.5 对齐复审（基线 `73576c5`）评审结论

- **评审日期**：2026-09-03
- **评审人**：muse（独立评审）
- **评审对象**：`2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md`，钉死 `73576c5`（HEAD `34a1077` 仅增申请/STATUS）
- **结论**：**授予轨 B L1 DOC-ALIGNED / PG-0。**
- **结构化 issue**：`BLOCKING` × 0、`ADVISORY` × 2（P3）

## 1. 用例正文稳定性核验

`git diff cd285dd..73576c5 -- docs/usercases` **空**——13 份用例正文零变更，申请"100% 稳定"属实。前序（`cd285dd`：claude/grok/qwen 三方一致 YES）授予基础未动。

## 2. 本轮运行时闭环与用例规范的一致性（独立探针）

申请 §1 称本轮打通"用例规范—代码运行时"闭环，逐项实测：

| 用例规范 | 运行时实现 | 一致性 |
|---|---|---|
| UC-5 §2.b 纯整数五重门禁（独裁帽 $3w_i<2W$、$E_N$/$E_W$ quorum、$3W_{win}\ge 2E_W$、胜方席位 ≥2） | `ConsensusEngine.evaluate`：门禁比较全为整数交叉乘法（`3*approve_weight >= 2*effective_weight` 等）；`test_weighted_counterexample_deadlock`（YES w=2 vs NO w=1+1 → DEADLOCK）、`test_weighted_minimum_winning_seats_enforcement` 均通过；`test_consensus` 5/5 | ✅ 一致（置信度等报告字段的浮点除法不参与门禁判定，属展示层） |
| UC-6 §2.b/c + UC-7 §2：APPROVED 含 issue 不得直跳 MERGING；FINAL 全 `requires_new_checkpoint=false` → E4，任一 true → E5a | `orchestrator.py:707-762`：有 FINAL 且全 false → E4；任一 true → E5a；无合法 FINAL → 发布 Type E `DISPOSITION_REQUIRED`（含 `vote_result_ref`+`issues_index_sha256`+`timeout_deadline`）并驻留 `CONSENSUS_CHECK`；集成测试 `test_approved_with_advisory_holds_and_requires_disposition` 通过 | ✅ 一致 |
| UC-1/UC-10 法定人数公式（N=4 → $\lceil 2N/3\rceil=3$） | 根 `macao.yaml` 双 quorum 已提至 3；`validate_config` → `(True, None)`；`test_root_macao_yaml_passes_semantic_validation` 通过 | ✅ 一致 |

## 3. 申请 §3 机验复核

97/97（41.4s，本机重放）、compileall 0、fixtures **10/10 + 22/22**（本机用 Draft-07 + 项目校验器双层重放：16 份契约层拦截、6 份语义层拦截，全部归因无 LEAK）、双 Schema 目录 0 diff、217 份 md 零控制字符——**全部为真**。

## 4. ADVISORY（P3）

- **A-1**：申请"212 份 Markdown"与受审树实计（`git ls-files "*.md"` = 205，本机工作区扫描 217 含申请文件本身增量）口径差；结论（0 控制字符）为真。计数问题连续多轮复发，建议固定命令口径。
- **A-2**：`orchestrator.py:483` 注释"APPROVED → … moves to MERGING (E4)"为旧文，与 :707 起的守卫代码不符；注释级残留，建议随手清理（行为以代码为准，无功能影响）。

## 5. 定级意见

用例正文零变更延续前序授予；本轮三处"规范—运行时"闭环均经独立探针证实一致；P0/P1 为零。

**授予轨 B L1 DOC-ALIGNED / PG-0**（累计 claude/grok/qwen 三方连续三轮一致）。

## Reviewer 自审记录

- 未采信"连续两轮全票通过即免检"：用例零变更经 diff 证实，三处运行时闭环逐项读码+跑测试验证；
- codex `cd285dd` REJECT 三项均为代码实施差距，本轮已在代码层实质落地（非仅文档承诺），分歧自然消解；
- 未覆盖：win32、Phase 1 实现。
